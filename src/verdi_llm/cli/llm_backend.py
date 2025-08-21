###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The implementation of all llm models for the `verdi smart` command line interface."""

import hashlib
import json
import os
from pathlib import Path

import click
import numpy as np
import requests
from time import time
from typing import Callable

LLM_DIRECTORY = Path.home() / ".aiida" / "llm"
VERDI_CLI_MAP = Path(__file__).resolve().parent / "verdi_cli.json"

__all__ = ["LLM_DIRECTORY", "RAG", "groc_command_generator", "VERDI_CLI_MAP"]


class RAG:
    def __init__(self):
        from sentence_transformers import SentenceTransformer

        self.json_path = VERDI_CLI_MAP

        # Load the JSON file
        with open(self.json_path, "r") as f:
            self.data = json.load(f)

        self.model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        self.build_or_load_embeddings()

    def _compute_file_hash(self):
        """Compute SHA256 hash of the JSON file to detect changes"""
        hash_sha256 = hashlib.sha256()
        with open(self.json_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def build_or_load_embeddings(self, suppress_warning=False):
        """Load or generate embeddings with caching.
        Assigns the embeddings and index to self.embeddings and self.index.
        """

        from faiss import read_index

        embeddings_path = LLM_DIRECTORY / "rag_embeddings.npy"
        index_path = LLM_DIRECTORY / "rag.index"
        hash_path = LLM_DIRECTORY / "rag.hash"

        current_hash = self._compute_file_hash()

        # Check if we can load cached version
        if all(os.path.exists(p) for p in [embeddings_path, index_path, hash_path]):
            with open(hash_path, "r") as f:
                saved_hash = f.read().strip()

            if saved_hash == current_hash:
                self.embeddings = np.load(embeddings_path)
                self.index = read_index(str(index_path))
                print("Loaded cached embeddings and index.")
                return

        if not suppress_warning:
            click.echo(
                "Cache not found, or invalid. Generating new embeddings and index."
            )

        texts = [
            f"Command and Usage{entry['command_usage']}\nDescription: {entry['description']}\n"
            f"Required Arguments: {entry['required_arguments']}\nOptions: {entry['options']}\n"
            for entry in self.data
        ]

        from faiss import IndexFlatIP, write_index

        self.embeddings = self.model.encode(texts, normalize_embeddings=True)
        self.index = IndexFlatIP(self.embeddings.shape[1])
        self.index.add(self.embeddings.astype(np.float32))

        # Save cache files
        np.save(embeddings_path, self.embeddings)
        write_index(self.index, str(index_path))
        with open(hash_path, "w") as f:
            f.write(current_hash)

    def retrieve(self, query, k=3):
        """
        Retrieve most relevant entries for a given query
        """
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(query_embedding.astype(np.float32), k)

        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx >= 0:  # FAISS might return -1 for invalid indices
                entry = self.data[idx]
                entry["score"] = float(score)
                results.append(entry)

        return sorted(results, key=lambda x: x["score"], reverse=True)


def executor_engine(command: str, executor: Callable):

    while True:
        try:
            action = input("\n[E]xecute, [M]odify, [C]ancel? ").lower().strip()
            if action.lower() == "e":
                executor(command)
                break
            elif action.lower() == "m":
                modified = input("Enter modified command: ").strip()
                if modified:
                    executor(modified)
                break
            elif action.lower() == "c":
                print("Operation cancelled.")
                break
            else:
                print("Please enter E, M, or C")
        except KeyboardInterrupt:
            print("^C")
            break


def groc_command_generator(sentence, api_key):
    """Generate a command using the Groq LLM."""

    rag = RAG()

    # Retrieve relevant information
    results = rag.retrieve(sentence, k=3)

    context_str = "\n\n"
    for entry in results:
        if entry["required_arguments"]:
            ra = f"\nRequired Arguments: {entry['required_arguments']}"
        else:
            ra = "No Required Arguments"
        context_str += (
            f"RAG Score: {entry['score']}\n"
            f"Command and Usage: {entry['command_usage']}\n"
            f"Description: {entry['description']}\n"
            f"ra"
            f"Options: {entry['options']}\n\n"
        )

    # print(f"Context: {context_str}")

    model = "llama3-8b-8192"
    endpoint = "https://api.groq.com/openai/v1/chat/completions"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that generates valid verdi commands."
                "Only and only respond with the complete command starting with 'verdi', absolutely not a word more. "
                "Do not overly include optional flags if not explicitly needed. "
                "Do not invent flags, if you don't find them explicitly in the listed options. "
                "If your confidence in the answer is low, just say: 'I don't know'."
                "Remember several arguments after a flag must be separated by spaces never a commas (,) for example: "
                "'--computer C1, C2' is wrong, but '--computer C1 C2' is correct.",
            },
            {
                "role": "user",
                "content": f"Generate a AiiDA verdi command to: {sentence}. Here is RAG context: {context_str} ",
            },
        ],
        "max_tokens": 100,
        "temperature": 0.5,  # Lower temperature for more deterministic output
    }

    response = requests.post(endpoint, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_json = response.json()
        suggestion = response_json["choices"][0]["message"]["content"].strip()
        # Ensure the command starts with verdi
        if not suggestion.startswith("verdi"):
            suggestion = "verdi " + suggestion
        return suggestion
    else:
        click.echo(
            f"Failed to generate command: {response.status_code} - {response.text}"
        )
        return None
