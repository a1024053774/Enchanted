# installed by muster
# managed by muster; reinstalling or updating the integration overwrites this file.
# add custom hooks beside this file instead of editing it.
# MUSTER_INTEGRATION_ID=droid
# MUSTER_INTEGRATION_VERSION=3

param([string]$Action = "")

if ($Action -ne "session") { exit 0 }
if ($env:MUSTER_ENV -ne "1") { exit 0 }
if ([string]::IsNullOrWhiteSpace($env:MUSTER_PANE_ID)) { exit 0 }

$inputText = [Console]::In.ReadToEnd()
try {
    $payload = if ([string]::IsNullOrWhiteSpace($inputText)) { $null } else { $inputText | ConvertFrom-Json }
} catch {
    $payload = $null
}

if ($null -eq $payload -or [string]::IsNullOrWhiteSpace($payload.session_id)) { exit 0 }

$seq = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$muster = if ([string]::IsNullOrWhiteSpace($env:MUSTER_BIN_PATH)) { "muster" } else { $env:MUSTER_BIN_PATH }
try {
    & $muster pane report-agent-session $env:MUSTER_PANE_ID --source muster:droid --agent droid --agent-session-id $payload.session_id --seq $seq 2>$null | Out-Null
} catch {
}
