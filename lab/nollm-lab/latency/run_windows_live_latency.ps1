param(
  [Parameter(Mandatory=$true)][ValidateSet('write','recall')][string]$Mode,
  [ValidateRange(1,12)][int]$StartAt = 1,
  [ValidateRange(1,12)][int]$Count = 12,
  [ValidateRange(1,4)][int]$Concurrency = 3,
  [string]$OpenClaw = "$env:LOCALAPPDATA\Programs\nodejs\openclaw.cmd",
  [string]$OutputRoot = "C:\Users\chaos\nollm_aold_latency_live_20260716"
)

$ErrorActionPreference = 'Stop'

$writes = @(
  @{scenario='W_COLD_AFTER_RESTART'; message='北辰发布看板的每日校对安排在上午八点半，由周霁负责。'},
  @{scenario='W_NEW_SINGLE'; message='远帆设备清单的季度复核固定在每季第一个周三下午两点。'},
  @{scenario='W_NEW_MULTI'; message='云杉会议室的门禁联系人是唐沐，备用投影仪存放在西侧储物柜。'},
  @{scenario='W_NEW_SINGLE'; message='澄海项目的例行风险复盘由许宁在每周二下午三点主持。'},
  @{scenario='W_NEW_SINGLE'; message='山岚资料库的外借登记每天十七点由顾言汇总。'},
  @{scenario='W_DENSE_LOCALITY'; message='青岚展厅的夜间巡查表放在接待台左侧第二个抽屉。'},
  @{scenario='W_REUSE'; message='北辰发布看板的每日校对安排在上午八点半，由周霁负责。'},
  @{scenario='W_REVISION_TRUE'; message='北辰发布看板的每日校对时间改为上午九点，仍由周霁负责，八点半的安排取消。'},
  @{scenario='W_ADDITIVE'; message='北辰发布看板还需要在每周五由林澈归档本周变更记录。'},
  @{scenario='W_NO_MEMORY'; message='刚才窗外的云很薄，午后的光线也很柔和。'},
  @{scenario='W_NEW_SINGLE'; message='海棠值班表的交接确认每天十八点十五分完成。'},
  @{scenario='W_NEW_MULTI'; message='星河实验室的安全巡检在周四上午十一点，耗材盘点在每月最后一个工作日下午进行。'}
)

$recalls = @(
  @{scenario='R_RELEVANT_COLD'; message='Alpha 项目 V3.9 的发布校验码是什么？'},
  @{scenario='R_RELEVANT_COLD'; message='CAOLD 广域余量验收的发布校验码是什么？'},
  @{scenario='R_RELEVANT_WARM'; message='青岚展厅的备用钥匙放在哪里？'},
  @{scenario='R_RELEVANT_WARM'; message='青岚展厅每天几点播放闭馆广播？'},
  @{scenario='R_RELEVANT_WARM'; message='Alpha 项目的发布风险评审和发布窗口分别是什么时间？'},
  @{scenario='R_RELEVANT_WARM'; message='青岚展厅发生设备故障时应该联系谁？'},
  @{scenario='R_DENSE_HIDDEN_PREVIEW'; message='青岚展厅的雨伞借用登记表是什么颜色的封面？'},
  @{scenario='R_DENSE_HIDDEN_PREVIEW'; message='青岚展厅的志愿者交接本放在哪个位置？'},
  @{scenario='R_NONE'; message='为什么晴天的天空通常看起来是蓝色的？'},
  @{scenario='R_NONE'; message='请用一句话解释什么是可逆决策。'},
  @{scenario='R_REPEATED_TOPIC'; message='Alpha 项目的变更冻结检查由谁主持，安排在什么时候？'},
  @{scenario='R_MULTI_FACT'; message='请概括青岚展厅灯光巡检、温湿度记录和无障碍通道检查的安排与负责人。'}
)

$cases = if ($Mode -eq 'write') { $writes } else { $recalls }
$last = [Math]::Min(12, $StartAt + $Count - 1)
$selected = @($cases[($StartAt - 1)..($last - 1)])
$runRoot = Join-Path $OutputRoot $Mode
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
$batch = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$receipts = Join-Path $runRoot "receipts-$batch.jsonl"

for ($offset = 0; $offset -lt $selected.Count; $offset += $Concurrency) {
  $jobs = @()
  $end = [Math]::Min($selected.Count, $offset + $Concurrency)
  for ($position = $offset; $position -lt $end; $position++) {
    $case = $selected[$position]
    $index = $StartAt + $position
    $session = "aold-latency-$($case.scenario)-$('{0:d2}' -f $index)-$batch"
    $stdout = Join-Path $runRoot "$session.json"
    $stderr = Join-Path $runRoot "$session.stderr.txt"
    $jobs += Start-Job -ArgumentList $OpenClaw,$session,$case.message,$case.scenario,$stdout,$stderr,$index -ScriptBlock {
      param($exe,$sessionId,$message,$scenario,$out,$err,$caseIndex)
      $started = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
      & $exe agent --agent main --session-id $sessionId --message $message --json --timeout 360 1> $out 2> $err
      [ordered]@{case_index=$caseIndex;scenario_id=$scenario;session_id=$sessionId;exit_code=$LASTEXITCODE;started_epoch_ms=$started;returned_epoch_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();stdout_bytes=(Get-Item $out).Length;stderr_bytes=(Get-Item $err).Length}
    }
  }
  $jobs | Wait-Job | Out-Null
  $jobs | Receive-Job | ForEach-Object { $_ | ConvertTo-Json -Compress | Add-Content -LiteralPath $receipts -Encoding utf8NoBOM }
  $jobs | Remove-Job -Force
}

$parsed = Get-Content -LiteralPath $receipts | ForEach-Object { $_ | ConvertFrom-Json }
if (@($parsed | Where-Object exit_code -ne 0).Count -ne 0) { throw "$Mode Live run contains failed main-agent turns" }
[ordered]@{mode=$Mode;batch=$batch;start_at=$StartAt;count=$selected.Count;concurrency=$Concurrency;receipts=$receipts;completed_epoch_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()} | ConvertTo-Json -Compress
