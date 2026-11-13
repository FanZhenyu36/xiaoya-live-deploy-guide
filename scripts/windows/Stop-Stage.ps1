. "$PSScriptRoot\Common.ps1"
$s = Get-GuideSettings
$record = Join-Path $s.runtime_root 'stage-process.json'
if (-not (Test-Path -LiteralPath $record)) { throw 'No process record. This script only stops the instance it started.' }
$r = Get-Content -LiteralPath $record -Raw -Encoding UTF8 | ConvertFrom-Json
$owner = Get-CimInstance Win32_Process -Filter "ProcessId=$([int]$r.pid)" -ErrorAction SilentlyContinue
if (-not $owner) { Write-Host '[OK] Recorded launcher is already stopped.'; exit 0 }
if ($owner.ExecutablePath -ne $r.python -or $owner.CommandLine -notmatch 'src\.main') {
    throw 'Process identity changed. Nothing was stopped.'
}
$actual = (Get-Process -Id ([int]$r.pid)).StartTime.ToUniversalTime()
if ([Math]::Abs(($actual - [DateTime]::Parse($r.started).ToUniversalTime()).TotalSeconds) -gt 2) {
    throw 'Process start time changed. Nothing was stopped.'
}
try {
    Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$($s.stage_port)/api/live/stop" -TimeoutSec 15 | Out-Null
} catch { Write-Warning 'Could not confirm Vidu hangup. Verify the Vidu console before leaving.' }
$children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$([int]$r.pid)" | Where-Object { $_.Name -like 'python*' -and $_.CommandLine -match 'src\.main' })
foreach ($child in $children) { Stop-Process -Id $child.ProcessId -ErrorAction SilentlyContinue }
Stop-Process -Id ([int]$r.pid) -ErrorAction SilentlyContinue
Write-Host '[OK] Stopped only the recorded stage instance. Other Python services were preserved.'
