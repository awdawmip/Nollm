"""Enterprise Math defaults for the shared project-memory API and CLI."""
from pathlib import Path

from project_memory import (
    KERNELS, SCOPE, decide, describe, encounter, excerpt, links, literal_matches, save, save_statement,
    stitch, unstitch, walk,
)
from project_memory import main as project_main


SAVED_FIELD = Path(__file__).resolve().parent / "field"


def main(argv=None):
    project_main(argv, default_field=SAVED_FIELD)


if __name__ == "__main__":
    main()
