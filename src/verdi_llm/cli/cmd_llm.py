"""The `verdi-llm` command line interface."""

import json
import subprocess
from time import time
from typing import Callable, Optional

import click

from .llm_backend import LLM_DIRECTORY, RAG, groc_command_generator, executor_engine


@click.group("verdi-llm")
def verdi_llm():
    """Use LLM to query to find out how to do things."""


def _validate_backend(ctx, param, value):
    """Validate the backend option."""
    value = value.lower() if value else None
    if value and value not in ["groq"]:
        raise click.BadParameter("The only available options are: [groq]")
    return value


def _prompt(message: str, validation: Optional[Callable] = None):
    """Prompt to user until the validation passes."""
    while True:
        value = click.prompt(message, type=str)
        if validation:
            try:
                validation(None, None, value)
            except click.BadParameter as e:
                click.echo(str(e))
                continue
        break
    return value


def _execute_command(command):
    """Execute a command via subprocess and print the output."""

    try:
        click.echo("$ " + command)
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        click.echo("Command output:")
        click.echo(result.stderr)
        click.echo(result.stdout)
    except subprocess.CalledProcessError as e:
        click.echo("Error running command:")
        click.echo(e.stderr)
    except Exception as e:
        click.echo("An unexpected error occurred:")
        click.echo(str(e))


def load_smart_config(func):
    """Decorator to load the smart config file."""

    def wrapper(*args, **kwargs):
        config_file = LLM_DIRECTORY / "config.json"
        if not config_file.exists():
            click.echo(
                "No configuration file found. Please run `verdi smart configure` first."
            )
            return None
        with config_file.open("r") as f:
            config_data = json.load(f)
        if config_data is None:
            click.echo(
                "No configuration file found. Please run `verdi smart configure` first."
            )
            return

        return func(config_data["backend"], config_data["api_key"], *args, **kwargs)

    return wrapper


@verdi_llm.command("configure")
@click.option(
    "-b",
    "--backend",
    type=str,
    required=False,
    help="The LLM backend to use. Available options: groq.",
    callback=_validate_backend,
)
@click.option(
    "--api-key", type=str, required=False, help="Your API key for the LLM backend."
)
@click.pass_context
def smart_configure(ctx, backend, api_key):
    """Choose and configure an LLM backend."""

    # Setup the credentials
    click.echo(
        "This command will help you choose and configure an LLM backend for AiiDA.\n"
    )
    if not backend:
        click.echo(
            "Please follow the instructions below to set up your preferred LLM backend."
        )
        click.echo("Step #1 Choose a backend:")
        click.echo("      groq")
        backend_choice = _prompt("Your choice", _validate_backend)

    if not api_key:
        click.echo(f"Step #2 Enter your API key for {backend_choice}:")
        api_key = _prompt("Your API key")

    config_file = LLM_DIRECTORY / "config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)

    config_data = {"backend": backend_choice, "api_key": api_key}
    with config_file.open("w") as f:
        json.dump(config_data, f)

    click.echo(
        f"Configuration saved to {config_file}. You can change it later by editing this file.\n"
    )

    RAG()  # Build the or embeddings

    click.echo(
        "You can now use the `verdi smart` command to interact with the LLM backend.\n"
    )


@verdi_llm.command("cli")
@click.argument("something-to-ask", type=str)
@load_smart_config
def smart_generate(backend, api_key, something_to_ask):
    """Generate a command based on a natural language something-to-ask."""

    start_time = time()
    if backend == "groq":
        suggestion = groc_command_generator(something_to_ask, api_key)
        print(
            f"💡 Suggested command (in {time()-start_time:.1f} seconds): \n{suggestion}\n"
        )
        executor_engine(suggestion, _execute_command)
    else:
        click.echo(
            "No valid backend found. Please run `verdi smart configure` to set up a backend."
        )


@verdi_llm.command("shell")
def smart_shell():
    """Launch an interactive shell with pre-loaded LLM capabilities."""
    import sys
    import signal
    from pathlib import Path

    shell_script = Path(__file__).parent / "verdi_llm_shell.py"

    if shell_script.exists():
        import subprocess

        original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

        try:
            subprocess.run(
                [sys.executable, str(shell_script)],
                preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_DFL),
            )
        finally:
            signal.signal(signal.SIGINT, original_sigint_handler)
    else:
        click.echo(
            "Shell script not found. Please ensure verdi_llm_shell.py is in the same directory."
        )
