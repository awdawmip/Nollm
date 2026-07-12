param(
  [string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd",
  [string]$SessionKey = "agent:main:aold-natural-chat-smoke",
  [string]$Message = "请记住：这个项目的发布窗口固定在每周三下午三点。"
)
$ErrorActionPreference = "Stop"
if ($Message -match "nollm_form_statement|调用工具|/tool|\{.*request") {
  throw "The smoke message must remain ordinary natural chat."
}
& $OpenClaw agent --session-key $SessionKey --message $Message --json --timeout 300
