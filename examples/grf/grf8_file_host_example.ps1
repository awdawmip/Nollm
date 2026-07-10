$env:PYTHONPATH = "$PSScriptRoot\..\..\reference\python;$PSScriptRoot\..\.."
@'
from pathlib import Path
from nollm.grf.facade import GRFFacade
root = Path("grf8_example_workspace")
source = Path("notes.md")
source.write_text("# Decision\nUse explicit admission.", encoding="utf-8")
facade = GRFFacade(root)
result = facade.capture_source(source, "2026-07-11T00:00:00Z")
print(result)
'@ | python -
