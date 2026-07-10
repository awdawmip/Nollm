from __future__ import annotations
import json
import tempfile
from pathlib import Path
from integrations.adapters.grf7r_facade_runtime import FacadeRuntimeAdapter
from integrations.adapters.grf7r2_long_running import _capture_request

def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nollm-grf8-host-") as temp:
        root=Path(temp); registry=root/"registry.jsonl"; outcomes={}
        for index, host in enumerate(("file_host","codex_fixture","openclaw_fixture")):
            adapter=FacadeRuntimeAdapter(root/host, root/f"{host}.jsonl", registry_path=registry)
            response=adapter.handle(host, _capture_request(index)); outcomes[host]=response.get("ok") is True; adapter.close()
    print(json.dumps({"hosts":outcomes,"all_contracts":all(outcomes.values())},sort_keys=True)); return 0 if all(outcomes.values()) else 1
if __name__ == "__main__": raise SystemExit(main())
