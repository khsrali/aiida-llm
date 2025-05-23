"""Expose the verdi-cli, for usage as `python -m aiida`"""

import sys

if __name__ == "__main__":
    from llm import verdi_llm

    sys.exit(verdi_llm())
