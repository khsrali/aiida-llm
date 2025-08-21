#!/usr/bin/env python3
"""
verdi-llm shell: A shell environment with pre-loaded SentenceTransformer
Usage: python verdi_llm_shell.py
"""

import os
import sys
import subprocess
import json
import readline
import atexit
from pathlib import Path

# Import your existing modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from llm_backend import RAG, groc_command_generator, LLM_DIRECTORY, executor_engine


class VerdiLLMShell:
    def __init__(self):
        # Setup readline for history
        self.setup_history()

        print("🚀 Initializing verdi-llm shell...")
        print("   Loading SentenceTransformer (this may take a few seconds)...")

        # Pre-load the RAG system (this does the heavy SentenceTransformer loading)
        try:
            self.rag = RAG()
            print("✅ SentenceTransformer loaded successfully!")
        except Exception as e:
            print(f"❌ Failed to load SentenceTransformer: {e}")
            self.rag = None

        # Load config
        self.config = self.load_config()
        if not self.config:
            print("⚠️  No configuration found. Run 'verdi-llm configure' first.")
            print("   You can still use the shell for regular commands.")

        print("\n🎯 verdi-llm shell ready!")
        print("   - Use 'cli <your question>' for AI assistance")
        print("   - Use arrow keys for command history")
        print("   - Type 'exit' or Ctrl+D to quit\n")

    def setup_history(self):
        """Setup readline history"""
        # History file path
        self.history_file = Path.home() / ".verdi_llm_history"

        # Load existing history if it exists
        if self.history_file.exists():
            try:
                readline.read_history_file(self.history_file)
            except Exception:
                pass

        # Set history length
        readline.set_history_length(1000)

        # Save history on exit
        atexit.register(self.save_history)

        # Enable default bash-like tab completion
        readline.parse_and_bind("tab: complete")
        # Use default completer delimiters for bash-like behavior
        readline.set_completer_delims(" \t\n`~!@#$%^&*()-=+[{]}\\|;:'\",<>?")

    def save_history(self):
        """Save command history to file"""
        try:
            readline.write_history_file(self.history_file)
        except Exception:
            pass

    def load_config(self):
        """Load the LLM configuration"""
        config_file = LLM_DIRECTORY / "config.json"
        if config_file.exists():
            with config_file.open("r") as f:
                return json.load(f)
        return None

    def handle_llm_command(self, query):
        """Handle LLM queries using pre-loaded RAG"""
        if not self.rag:
            print("❌ SentenceTransformer not loaded. Cannot process LLM queries.")
            return

        if not self.config:
            print("❌ No configuration found. Run 'verdi-llm configure' first.")
            return

        try:
            suggestion = groc_command_generator(query, self.config["api_key"])

            print(f"💡 Suggested command:\n{suggestion}")
            executor_engine(suggestion, self.execute_command)

        except Exception as e:
            print(f"❌ Error processing LLM query: {e}")

    def execute_command(self, command):
        """Execute a system command"""
        try:
            print(f"$ {command}")
            result = subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=False,  # Let output go directly to terminal
            )
            if result.returncode != 0:
                print(f"Command exited with code {result.returncode}")
        except KeyboardInterrupt:
            print()
        except Exception as e:
            print(f"Error executing command: {e}")

    def run(self):
        """Main shell loop"""
        while True:
            try:
                # Get current directory for prompt
                cwd = os.getcwd()
                home = os.path.expanduser("~")
                if cwd.startswith(home):
                    display_cwd = "~" + cwd[len(home) :]
                else:
                    display_cwd = cwd

                # Show prompt using input() with colors - readline will handle history
                prompt = f"\033[1;32mverdi-llm\033[0m:\033[1;34m{display_cwd}\033[0m$ "

                try:
                    command = input(prompt).strip()
                except KeyboardInterrupt:
                    print("^C")
                    continue

                if not command:
                    continue

                # Handle special commands
                if command in ["exit", "quit"]:
                    break
                elif command.startswith("cli "):
                    # Extract the query after 'cli '
                    query = command[4:].strip()
                    if query:
                        self.handle_llm_command(query)
                    else:
                        print("Usage: cli <your question>")
                elif command.startswith("cd "):
                    # Handle cd specially to change directory in this process
                    try:
                        path = command[3:].strip()
                        if path:
                            os.chdir(os.path.expanduser(path))
                        else:
                            os.chdir(os.path.expanduser("~"))
                    except Exception as e:
                        print(f"cd: {e}")
                else:
                    # Execute regular system command
                    self.execute_command(command)

            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Shell error: {e}")
                continue

        print("👋 Exiting verdi-llm shell")


if __name__ == "__main__":
    shell = VerdiLLMShell()
    shell.run()
