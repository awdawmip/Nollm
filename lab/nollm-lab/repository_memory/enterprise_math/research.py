"""Enterprise Math alias for the shared project-memory API and explicit field CLI."""
from project_memory import (
    KERNELS, SCOPE, decide, describe, encounter, excerpt, links, literal_matches, save, save_statement,
    stitch, unstitch, walk,
)
from project_memory import main as project_main


def main(argv=None):
    project_main(argv)


if __name__ == "__main__":
    main()
