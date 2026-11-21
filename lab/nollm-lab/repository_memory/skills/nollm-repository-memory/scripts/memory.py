"""Use native project memory; select source tools or comparison baselines explicitly."""
import argparse
from pathlib import Path
import runpy
import sys


NATIVE_TOOLS = {
    "project": "project_memory.py",
    "em": "enterprise_math/research.py",
}
NOTE_COMMANDS = ("brief", "source", "inventory", "capture", "review", "status", "view")
AUXILIARY_TOOLS = {
    "facts": "facts.py",
    "records": "records.py",
    "route": "router.py",
    "coverage": "coverage_cli.py",
    "check-marks": "check_marks.py",
    "aoci": "geometry_cli.py",
    "aoci-field": "native_geo.py",
}
BASELINE_TOOLS = {
    "recall": "task_recall.py",
    "field": "machine_field.py",
}
LEGACY_COMMANDS = {
    **{name: f"aux {name}" for name in (*NOTE_COMMANDS, *AUXILIARY_TOOLS)
       if name not in ("aoci", "aoci-field")},
    **{name: f"baseline {name}" for name in BASELINE_TOOLS},
    "geometry": "aux aoci",
    "geometry-native": "aux aoci-field",
}


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Native memory: project --field FIELD encounter --cursor-file SESSION. "
               "project/em use Surface and a Host-selected physical entry; "
               "aux and baseline are separate, opt-in workflows.",
    )
    parser.add_argument("command", choices=(*NATIVE_TOOLS, "aux", "baseline"),
                        help="project: native field; em: native research field; "
                             "aux: source/geometry tools; baseline: heuristic comparisons")
    if len(sys.argv) > 1 and sys.argv[1] in LEGACY_COMMANDS:
        old = sys.argv[1]
        parser.error(f"'{old}' moved to '{LEGACY_COMMANDS[old]}'. "
                     "It is an explicit auxiliary/baseline workflow. "
                     "For native memory use 'project --field FIELD encounter --cursor-file SESSION'.")
    args = parser.parse_args(sys.argv[1:2])
    if args.command in NATIVE_TOOLS:
        target = NATIVE_TOOLS[args.command]
        del sys.argv[1]
    else:
        auxiliary = args.command == "aux"
        tools = AUXILIARY_TOOLS if auxiliary else BASELINE_TOOLS
        group = argparse.ArgumentParser(
            prog=f"{parser.prog} {args.command}",
            description=("Explicit source navigation, evidence and geometry tooling."
                         if auxiliary else
                         "Comparison baselines with lexical/source/graph entry selection and layout."),
        )
        group.add_argument("tool", choices=(*NOTE_COMMANDS, *tools) if auxiliary else tuple(tools))
        selected = group.parse_args(sys.argv[2:3]).tool
        if auxiliary and selected in NOTE_COMMANDS:
            target = "repo_notes.py"
            del sys.argv[1]
        else:
            target = tools[selected]
            del sys.argv[1:3]

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

    runpy.run_path(str(runtime / target), run_name="__main__")


if __name__ == "__main__":
    main()
