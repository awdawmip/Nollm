# Nollm OpenClaw 插件错误知识库

**日期**：2026-07-11  
**用途**：Nollm GRF Adapter 的安装、更新、运行、Hook、Tool、LLM Placement 与日志故障定位。  
**开发环境**：Windows 10/11 + PowerShell。  
**联网基线**：截至 2026-07-11，OpenClaw 官方最新稳定版为 `v2026.6.11`；实际执行时必须重新查询本机版本和更新状态。

本知识库只服务工程定位，不扩展为安全或供应链审计系统。

---

# 0. 固定诊断顺序

遇到插件问题时，不要直接改代码。先按顺序收集事实：

```powershell
node --version
npm --version
openclaw --version
openclaw update status --json

openclaw gateway status --deep --require-rpc
openclaw health

openclaw plugins list --enabled --verbose
openclaw plugins inspect nollm-grf --runtime --json

openclaw doctor --lint --json
openclaw logs --limit 500 --json
```

实时观察：

```powershell
openclaw logs --follow --json
```

频道问题：

```powershell
openclaw channels logs --channel all --lines 500 --json
```

必须区分：

```text
plugins list / 普通 inspect：
  主要证明冷配置和注册表状态

plugins inspect <id> --runtime --json：
  证明正在运行的 Gateway 实际加载了哪些 Hook、Tool 和 Service
```

---

# 1. 建议日志配置

OpenClaw 主要有：

```text
Gateway JSONL 文件日志
Gateway 控制台日志
```

Windows 开发环境应配置明确路径，不依赖临时目录：

```json5
{
  logging: {
    level: "info",
    consoleLevel: "info",
    consoleStyle: "pretty",
    file: "C:\\Users\\<user>\\.openclaw\\logs\\openclaw.log"
  }
}
```

插件统一使用：

```typescript
api.logger.debug(...)
api.logger.info(...)
api.logger.warn(...)
api.logger.error(...)
```

每条 Nollm 关键日志至少带：

```text
plugin_id
hook
session_id
run_id
host_request_id
placement_request_id
shard_id
action
provider
model
latency_ms
error_code
```

日志用于定位，不是 Nollm 事实源。

---

# 2. 插件已安装，但 Hook 不运行

## 症状

```text
plugins list 能看到 nollm-grf
message_received / agent_end 没有日志
工具不可见
```

## 确认命令

```powershell
openclaw gateway status --deep --require-rpc
openclaw plugins inspect nollm-grf --runtime --json
openclaw logs --follow --json
```

## 常见原因

```text
Gateway 未重启
插件被 disabled
plugins.allow 未包含插件 id
plugins.deny 覆盖 allow
运行中的 Gateway 不是当前配置对应实例
入口文件未 build
manifest 与 package entry 不一致
Hook 注册代码未执行
```

## 修复

```powershell
openclaw plugins enable nollm-grf
openclaw gateway restart
openclaw plugins inspect nollm-grf --runtime --json
```

本地开发安装：

```powershell
openclaw plugins install --link .\integrations\openclaw\grf-adapter
```

修改 TypeScript 后：

```powershell
pnpm --dir .\integrations\openclaw\grf-adapter build
openclaw gateway restart
```

---

# 3. Manifest 或插件配置无效

## 症状

```text
Gateway 启动失败
config validation error
unknown plugin id
contracts.tools mismatch
plugin present but blocked
```

## 确认

```powershell
openclaw doctor --lint --json
openclaw plugins inspect nollm-grf --json
openclaw logs --limit 300 --json
```

## 常见原因

```text
openclaw.plugin.json 缺必填字段
configSchema.additionalProperties=false 但遗漏实际配置项
contracts.tools 未声明 registerTool 的名称
package.json 的 openclaw.extensions 指向错误入口
旧 plugin id 仍留在 openclaw.json
workspace plugin 未显式 enable
```

## 修复原则

```text
先修 manifest / schema；
再重新 build；
再 restart Gateway；
最后 runtime inspect。
```

`openclaw doctor --fix` 只用于已理解的 stale config，不用它掩盖 Schema 设计错误。

---

# 4. TypeScript 插件 import 失败

## 症状

```text
Cannot find module
ERR_MODULE_NOT_FOUND
requires compiled runtime output
dependency import failed
```

## 常见原因

```text
只提交 .ts，未生成 dist
package.json 指向不存在的文件
type 不是 module
依赖未安装
从其他插件导入 private SDK
Node 版本不满足当前 OpenClaw
```

## 修复

```powershell
pnpm --dir .\integrations\openclaw\grf-adapter install
pnpm --dir .\integrations\openclaw\grf-adapter build
```

检查：

```text
package.json: type=module
openclaw.extensions 指向 build 后 JS
dist 已包含在本地安装目录
peerDependencies.openclaw 与实际版本兼容
Node 满足当前官方要求
```

不得通过导入其他插件私有源码解决公共 API 缺失。

---

# 5. 工具未出现在模型上下文

## 症状

```text
runtime inspect 显示插件已加载
模型仍看不到 nollm_prepare_placement 或 nollm_apply_placement
```

## 检查

```text
openclaw.plugin.json contracts.tools
api.registerTool 名称
plugins.entries.nollm-grf.enabled
plugins.allow / plugins.deny
tools.allow / tools.deny / tools.alsoAllow
当前 Agent tool profile
sandbox tool policy
```

## 命令

```powershell
openclaw plugins inspect nollm-grf --runtime --json
openclaw doctor --lint --json
openclaw logs --follow --json
```

Manifest 声明和运行时注册必须完全一致。

---

# 6. `llm-task` 不可用

## 症状

```text
tool not found: llm-task
Placement Skill 无法发起结构化模型调用
```

## 参考配置

```json5
{
  plugins: {
    entries: {
      "llm-task": {
        enabled: true,
        config: {
          defaultProvider: "<provider>",
          defaultModel: "<provider/model>",
          allowedModels: ["<provider/model>"],
          maxTokens: 800,
          timeoutMs: 45000
        }
      }
    }
  },
  tools: {
    alsoAllow: ["llm-task"]
  }
}
```

然后：

```powershell
openclaw gateway restart
openclaw plugins inspect llm-task --runtime --json
```

## 禁止

```text
插件内部 shell 调用递归 openclaw.invoke
绕过 OpenClaw 直接请求供应商 HTTP API
Python 规则替代模型决策
```

优先工作流：

```text
nollm_prepare_placement
→ Agent/Skill 调用 llm-task
→ nollm_apply_placement
```

如果实际 Plugin SDK 提供受支持的内部模型调用 helper，必须先在实机发现报告中确认，再采用。

---

# 7. PlacementDecision JSON 解析失败

## 症状

```text
invalid JSON
schema validation failed
missing action
additional property rejected
identity 格式错误
```

## 处理

第一次失败：

```text
允许一次 JSON 格式修复调用
```

第二次仍失败：

```text
action = defer
error_code = invalid_decision
Core 不 mutation
```

记录：

```text
实际 provider/model
Schema 错误路径
原始输出长度
是否执行修复
最终 defer 原因
```

不得根据文本关键词推测 action。

---

# 8. 模型超时或 Provider 不可用

## 症状

```text
model_timeout
provider unavailable
authentication failure
stream ended before JSON
```

## 常规日志

```powershell
openclaw logs --follow --json
```

## 临时传输调试

```powershell
$env:OPENCLAW_DEBUG_MODEL_TRANSPORT="1"
$env:OPENCLAW_DEBUG_MODEL_PAYLOAD="tools"
$env:OPENCLAW_DEBUG_SSE="events"

openclaw gateway --verbose --ws-log compact
```

需要查看原始模型流时，仅在开发环境使用：

```powershell
openclaw gateway --raw-stream --raw-stream-path .\openclaw-model-stream.jsonl
```

## 业务语义

```text
Capture 保持成功
Placement 返回 defer / unavailable
Core 不执行 placement mutation
```

---

# 9. Hook 超时或 Gateway 卡顿

## 症状

```text
用户消息明显延迟
agent_end 很久不返回
Hook timeout
Gateway shutdown 等待插件
```

## 常见原因

```text
message_received 中同步执行 LLM Placement
agent_end 中等待长模型调用
tool factory 预加载大型 Python 依赖或语料
gateway_stop 执行无界任务
```

## 正确拆分

```text
message_received：
  快速 Capture / 入队

agent_end：
  捕获最终输出并排队

agent_turn_prepare：
  消费可用的局部 recall / placement 结果

实际 LLM Placement：
  Tool / Skill / next-turn workflow
```

示例 Hook 超时配置：

```json5
{
  plugins: {
    entries: {
      "nollm-grf": {
        hooks: {
          timeoutMs: 30000,
          timeouts: {
            message_received: 10000,
            agent_end: 15000,
            gateway_stop: 10000
          }
        }
      }
    }
  }
}
```

---

# 10. Agent 准备工具时变慢

临时开启：

```powershell
openclaw config set logging.level trace
openclaw logs --follow
```

搜索：

```text
[trace:plugin-tools] factory timings
```

如果 Nollm factory 慢，将以下动作移到实际执行阶段：

```text
Python bridge 连接
Placement corpus 加载
大型 Schema 编译
文件系统扫描
Core health check
```

Tool factory 只返回轻量 schema 和 handler。

---

# 11. `message_received` 内容不正确

不要解析旧的扁平 plaintext envelope。

应使用实际 Hook 类型中的结构化字段，例如：

```text
BodyForAgent
结构化 user-context blocks
threadId
messageId
senderId
metadata
```

协议中应区分：

```text
频道原始正文
交给 Agent 的正文
```

Capture 哪一份必须明确，不能悄悄替换。

---

# 12. 助手输出重复 Capture

## 可能原因

```text
agent_end 与 message_sent 都 Capture
流式中间块被当成最终输出
Gateway retry
跨频道 mirrored delivery
```

## 规则

```text
agent_end：
  捕获最终自然回答

message_sent：
  只观察投递成功/失败

使用 runId + final message identity 幂等

不捕获 progress preview
```

---

# 13. Tool result 重复或过大

使用：

```text
after_tool_call
```

观察结果、错误和耗时。

Capture 策略：

```text
结构化小结果：
  保存 exact result

大型结果：
  保存 source reference + 必要窗口

流式结果：
  只在最终完成事件 Capture
```

不得把全部工具调试日志自动长期保存。

---

# 14. Session 重启后 Placement queue 丢失

相关 Hook：

```text
session_start
session_end
gateway_start
gateway_stop
```

`session_end.reason` 可能包括：

```text
restart
shutdown
reset
compaction
idle
daily
deleted
```

Placement queue 需要文件持久化；Gateway 启动后恢复。

OpenClaw session_id 只能映射 Nollm context ref，不得作为 EvidenceIdentity 或全局 route。

---

# 15. 兼容 Hook 警告

新代码优先：

```text
before_model_resolve
agent_turn_prepare
before_prompt_build
gateway_stop
```

不要把以下兼容面作为新主路径：

```text
before_agent_start
deactivate
```

若实际安装版本 API 不同，以本机 Plugin SDK 类型和官方文档为准，并记录在 Runtime Discovery Report。

---

# 16. 插件更新后行为变化

固定更新流程：

```powershell
openclaw update --dry-run --json
openclaw update
openclaw doctor
openclaw gateway restart
openclaw health
openclaw plugins inspect nollm-grf --runtime --json
```

随后运行：

```text
插件安装 smoke
Hook smoke
llm-task JSON smoke
Placement development corpus
Placement evaluation holdout
无索引 Recall smoke
```

不能只以 Gateway 启动成功作为兼容性通过。

---

# 17. `diagnose.ps1` 必须输出

```text
OpenClaw version
update channel/status
Node version
Gateway deep status
health
plugin installed/enabled
runtime hooks/tools/services
llm-task runtime state
configured provider/model
Nollm Core path
Nollm storage root
Gateway log path
last 50 Nollm plugin errors
last Placement request/result
pending Placement queue count
```

诊断与修复分离；`diagnose.ps1` 不自动修改配置。

---

# 18. 错误码建议

Nollm Adapter 至少区分：

```text
openclaw_cli_missing
gateway_unreachable
gateway_unhealthy
plugin_not_installed
plugin_not_loaded
plugin_disabled
plugin_contract_mismatch
hook_not_registered
tool_not_available
llm_task_unavailable
model_unavailable
model_timeout
invalid_decision
unknown_identity
illegal_geometry_address
core_rejected
deferred
```

`deferred` 是业务结果，不是系统故障。

---

# 19. 何时必须停止并回报

真实环境阻断：

```text
OpenClaw CLI 不存在
Node 版本不满足实际 OpenClaw
Gateway 无法启动
Plugin SDK 与安装版本不兼容
实际 Plugin API 不支持所需 Hook/Tool
实际模型无法调用
llm-task 或其他官方结构化模型面不可用
```

以下不停止整个任务：

```text
Prompt 指标暂时不足
少量 case defer
日志字段缺失
安装脚本小问题
普通测试失败
```

这些在任务内修复。
