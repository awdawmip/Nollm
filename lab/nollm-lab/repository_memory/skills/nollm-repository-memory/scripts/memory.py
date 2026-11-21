"""Read and maintain Nollm repository memory from a checkout or installed skill."""
import argparse
from pathlib import Path
import runpy
import sys


TOOLS = {
    "project": "project_memory.py",
    "em": "enterprise_math/research.py",
    "recall": "task_recall.py",
    "facts": "facts.py",
    "records": "records.py",
    "route": "router.py",
    "field": "machine_field.py",
    "coverage": "coverage_cli.py",
    "check-marks": "check_marks.py",
    "geometry": "geometry_cli.py",
    "geometry-native": "native_geo.py",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("brief", "source", "inventory", "capture",
                                            "review", "status", "view", *TOOLS))
    args = parser.parse_args(sys.argv[1:2])

    scripts = Path(__file__).resolve().parent
    runtime = scripts / "runtime"
    if runtime.is_dir():
        sys.path.insert(0, str(runtime))
    else:
        # In the Nollm checkout, use the same implementation that gets packaged.
        runtime = scripts.parents[2]
        packages = runtime.parents[2] / "packages"
        sys.path[:0] = [str(runtime), str(packages / "nollm-core" / "src"),
                        str(packages / "nollm-access" / "src")]

    if args.command in TOOLS:
        del sys.argv[1]
        runpy.run_path(str(runtime / TOOLS[args.command]), run_name="__main__")
    else:
        runpy.run_path(str(runtime / "repo_notes.py"), run_name="__main__")


if __name__ == "__main__":
    main()
