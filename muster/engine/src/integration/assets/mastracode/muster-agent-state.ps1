# installed by muster
# managed by muster; reinstalling or updating the integration overwrites this file.
# add custom hooks beside this file instead of editing it.
# MUSTER_INTEGRATION_ID=mastracode
# MUSTER_INTEGRATION_VERSION=2

param([string]$Action = "")

if ($Action -notin @("session", "working", "idle", "blocked")) { exit 0 }
if ($env:MUSTER_ENV -ne "1") { exit 0 }
if ([string]::IsNullOrWhiteSpace($env:MUSTER_PANE_ID)) { exit 0 }

$inputText = [Console]::In.ReadToEnd()
try {
    $payload = if ([string]::IsNullOrWhiteSpace($inputText)) { $null } else { $inputText | ConvertFrom-Json }
} catch {
    $payload = $null
}

$sessionId = if ($null -ne $payload -and $payload.session_id -is [string]) { $payload.session_id } else { $null }
$seq = [DateTime]::UtcNow.Ticks
$muster = if ([string]::IsNullOrWhiteSpace($env:MUSTER_BIN_PATH)) { "muster" } else { $env:MUSTER_BIN_PATH }
try {
    if ($Action -eq "session") {
        if ([string]::IsNullOrWhiteSpace($sessionId)) { exit 0 }
        & $muster pane report-agent-session $env:MUSTER_PANE_ID --source muster:mastracode --agent mastracode --seq $seq --session-start-source startup --agent-session-id $sessionId 2>$null | Out-Null
    } else {
        $args = @("pane", "report-agent", $env:MUSTER_PANE_ID, "--source", "muster:mastracode", "--agent", "mastracode", "--state", $Action, "--seq", "$seq")
        if (-not [string]::IsNullOrWhiteSpace($sessionId)) {
            $args += @("--agent-session-id", $sessionId)
        }
        & $muster @args 2>$null | Out-Null
    }
} catch {
}
