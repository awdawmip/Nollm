$ErrorActionPreference = 'Stop'
openclaw plugins enable nollm-grf
openclaw gateway restart
openclaw plugins inspect nollm-grf --runtime --json
