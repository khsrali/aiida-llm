import asyncio
import json
import re
from pathlib import Path

VERDI_CLI_MAP = Path(__file__).resolve().parent / "verdi_cli.json"
CONCURRENCY_LIMIT = 10  # Adjust based on your system capabilities

__all__ = ["VERDI_CLI_MAP"]


def parse_usage_and_required_args(lines):
    """Extract the usage line and required arguments from the help text."""
    usage_line = ""
    required_args = []

    for line in lines:
        if line.startswith("Usage: "):
            usage_line = line[len("Usage: ") :].strip()
            break

    if usage_line:
        # Extract required arguments (uppercase words in usage that aren't OPTIONS, COMMAND, ARGS)
        # Pattern to find uppercase words that are likely required arguments
        args_pattern = r"\b([A-Z][A-Z_]*)\b"
        potential_args = re.findall(args_pattern, usage_line)

        # Filter out common CLI patterns that aren't actual arguments
        exclude_patterns = {"OPTIONS", "COMMAND", "ARGS", "PROFILE"}

        for arg in potential_args:
            if arg not in exclude_patterns:
                # Try to infer description based on common patterns
                if arg == "COMPUTER":
                    description = "The computer to configure"
                elif arg == "CODE":
                    description = f"The {arg.lower()} to use"
                elif arg == "NODE":
                    description = f"The {arg.lower()} identifier"
                elif arg == "GROUP":
                    description = f"The {arg.lower()} to use"
                else:
                    description = f"The {arg.lower()} argument"

                required_args.append(f"{arg}: {description}")

    return usage_line, required_args


def parse_description(lines):
    """Extract the description from the help text, stopping at Options or Commands."""
    description = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith(("Options:", "Commands:")):
            break
        if stripped_line and not line.startswith("Usage: "):
            description.append(stripped_line)
    return " ".join(description)


def parse_options(lines):
    """Parse the options section into a list of optional flags and descriptions."""
    options = []
    in_options = False
    current_option = None

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("Options:"):
            in_options = True
            continue
        if in_options:
            # Check if we've moved to a new section
            if stripped_line.startswith(("Commands:", "Arguments:")) or (
                stripped_line and not line.startswith(" ")
            ):
                break
            # Process option lines
            if stripped_line.startswith("-"):
                parts = re.split(r"\s{2,}", stripped_line, 1)
                flags = parts[0].strip()
                desc = parts[1].strip() if len(parts) > 1 else ""

                # Skip help option
                if "-h" in flags or "--help" in flags:
                    continue

                # Format flags nicely
                flag_parts = [f.strip() for f in flags.split(",")]
                formatted_flags = " / ".join(flag_parts)

                current_option = f"{formatted_flags}: {desc}"
                options.append(current_option)
            elif current_option and stripped_line:
                # Continue description on next line
                options[-1] += " " + stripped_line

    return options


def parse_sub_commands(lines):
    """Parse the sub-commands section into a list of command names."""
    sub_commands = []
    in_commands = False

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("Commands:"):
            in_commands = True
            continue
        if in_commands:
            if stripped_line.startswith(("Options:", "Arguments:")) or (
                stripped_line and not line.startswith(" ")
            ):
                break
            if stripped_line:
                parts = re.split(r"\s{2,}", stripped_line, 1)
                if parts:
                    sub_commands.append(parts[0].strip())
    return sub_commands


async def get_help_output(command_path):
    """Async version of subprocess execution with timeout handling"""
    cmd = ["verdi"] + command_path + ["--help"]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        return stdout.decode().strip()
    except Exception as e:
        print(f"Error executing {' '.join(cmd)}: {e!s}")
        return ""


async def process_command(command_path, semaphore, entries):
    """Process a command and its sub-commands recursively with async"""

    print(f"Processing command: {' '.join(command_path)}")

    async with semaphore:
        help_text = await get_help_output(command_path)

    if not help_text:
        return

    lines = help_text.split("\n")
    usage, required_args = parse_usage_and_required_args(lines)
    description = parse_description(lines)
    options = parse_options(lines)
    sub_commands = parse_sub_commands(lines)

    # Process sub-commands recursively
    if sub_commands:
        sub_tasks = []
        for sub_cmd in sub_commands:
            sub_tasks.append(
                process_command(command_path + [sub_cmd], semaphore, entries)
            )
        await asyncio.gather(*sub_tasks)
    else:
        # This is a leaf command - create an entry
        full_command = "verdi " + " ".join(command_path)

        entry = {
            "command_usage": usage,
            "description": description.strip(),
            "required_arguments": required_args,
            "options": options,
        }
        entries.append(entry)


async def main():
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    entries: list[dict] = []

    await process_command([], semaphore, entries)

    with open(VERDI_CLI_MAP, "w") as f:
        json.dump(entries, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
