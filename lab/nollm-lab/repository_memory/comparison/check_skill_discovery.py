"""Check installed skill discovery using the selected hosts' real CLI catalogs."""
import argparse
import asyncio
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


LAB = Path(__file__).resolve().parents[1]
NAME = "nollm-repository-memory"


async def codex_catalog(exe, repo, env):
    proc = await asyncio.create_subprocess_exec(
        exe, "app-server", "--listen", "stdio://", cwd=repo, env=env,
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    async def rpc(message):
        proc.stdin.write(json.dumps(message).encode() + b"\n")
        await proc.stdin.drain()
        if "id" in message:
            while line := await proc.stdout.readline():
                reply = json.loads(line)
                if reply.get("id") == message["id"]:
                    return reply["result"]
            raise RuntimeError("Codex closed the connection before responding")

    try:
        await rpc({"id": 1, "method": "initialize", "params": {
            "clientInfo": {"name": "nollm-discovery-check", "version": "1"}}})
        await rpc({"method": "initialized"})
        listed = await rpc({"id": 2, "method": "skills/list", "params": {
            "cwds": [str(repo)], "forceReload": True}})
        return listed["data"][0]["skills"]
    finally:
        if proc.returncode is None:
            proc.kill()
        await proc.wait()


def list_skill(host, exe, repo, env):
    def run(*args, stdin=None):
        return subprocess.run([exe, *args], cwd=repo, env=env, input=stdin, capture_output=True,
                              text=True, check=True, timeout=45).stdout

    if host == "codex":
        rows = asyncio.run(asyncio.wait_for(codex_catalog(exe, repo, env), timeout=45))
    elif host == "claude":
        message = {"type": "control_request", "request_id": "catalog",
                   "request": {"subtype": "initialize"}}
        lines = run("--print", "--input-format", "stream-json", "--output-format", "stream-json",
                    "--verbose", "--no-session-persistence", stdin=json.dumps(message) + "\n")
        reply = next(row for row in map(json.loads, lines.splitlines())
                     if row["type"] == "control_response" and row["response"]["request_id"] == "catalog")
        rows = reply["response"]["response"]["commands"]
    elif host == "copilot":
        rows = json.loads(run("skill", "list", "--json"))
    else:
        rows = json.loads(run("debug", "skill"))
    return [row for row in rows if row["name"] == NAME and row.get("enabled", True)]


def check(host, exe, root, scope):
    home, repo = root / "user", root / "project"
    repo.mkdir(parents=True)
    codex_home = home / ".codex"
    codex_home.mkdir(parents=True)
    # Give each run a new, trusted checkout and no inherited accounts or plugins.
    env = {key: os.environ[key] for key in ("PATH", "LANG", "SystemRoot") if key in os.environ}
    env.update(HOME=str(home), USERPROFILE=str(home), CODEX_HOME=str(codex_home),
               XDG_CONFIG_HOME=str(home / ".config"), XDG_CACHE_HOME=str(home / ".cache"),
               XDG_DATA_HOME=str(home / ".local/share"), XDG_STATE_HOME=str(home / ".local/state"),
               CLAUDE_CONFIG_DIR=str(home / ".claude"), CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1",
               DISABLE_AUTOUPDATER="1", OPENCODE_DISABLE_MODELS_FETCH="1")
    (codex_home / "config.toml").write_text(f'[projects.{json.dumps(str(repo))}]\ntrust_level = "trusted"\n')
    subprocess.run(["git", "init", "-q", repo], env=env, check=True)
    if list_skill(host, exe, repo, env):
        raise ValueError(f"{host}: skill existed before installation")

    command = [sys.executable, LAB / "install_skill.py", "--host", host, "--scope", scope]
    directory = Path(subprocess.check_output(command, env=env, cwd=repo, text=True).strip())
    rows = list_skill(host, exe, repo, env)
    if len(rows) != 1:
        raise ValueError(f"{host}: expected one enabled skill, found {len(rows)}")
    row = rows[0]
    if host == "claude":
        label = "project" if scope == "repo" else "user"
        if not row["description"].endswith(f"({label})"):
            raise ValueError(f"Claude reported the wrong scope: {row['description']}")
    elif host == "copilot":
        if Path(row["path"]).resolve() != directory.resolve():
            raise ValueError(f"Copilot reported a different skill directory: {row['path']}")
    else:
        file = row["path"] if host == "codex" else row["location"]
        if Path(file).resolve() != (directory / "SKILL.md").resolve():
            raise ValueError(f"{host} reported a different skill file: {file}")
    metadata = {key: row[key] for key in ("name", "description", "enabled", "scope", "source",
                                          "path", "location", "argumentHint") if key in row}
    for key in ("path", "location"):
        if key in metadata:
            metadata[key] = str(Path(metadata[key]).relative_to(root))
    return {"scope": scope, "before": [], "after": [metadata],
            "installed_skill_sha256": sha256((directory / "SKILL.md").read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hosts", nargs="+", choices=("codex", "claude", "copilot", "opencode"))
    args = parser.parse_args()
    report = {}
    for host in args.hosts:
        exe = shutil.which(host)
        if not exe:
            parser.error(f"{host} CLI is required on PATH")
        version = subprocess.check_output([exe, "--version"], text=True, timeout=45).splitlines()[0]
        with TemporaryDirectory(prefix="nollm-skill-discovery-") as temp:
            observations = [check(host, exe, Path(temp) / scope, scope) for scope in ("repo", "user")]
        report[host] = {"version": version, "catalog_checks": observations}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
