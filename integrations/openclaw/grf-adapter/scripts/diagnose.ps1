$ErrorActionPreference = 'Stop'
openclaw --version
openclaw gateway status --deep --require-rpc
openclaw plugins inspect nollm-grf --runtime --json
openclaw plugins inspect llm-task --runtime --json
