param([string]$Room='')
. "$PSScriptRoot\Common.ps1"
$s = Get-GuideSettings
Set-LocalEnvironment
if (-not $Room) { $Room = [string]$s.room }
if (-not $Room) { $Room = Read-Host 'Full Douyin live URL or numeric room ID' }
$Room = $Room.Trim()
if ($Room -match '^https?://live\.douyin\.com/(\d+)(?:[/?#].*)?$') { $Room = $Matches[1] }
if ($Room -notmatch '^\d+$') { throw 'Use a numeric room ID or https://live.douyin.com/ID URL.' }
if (-not (Test-StageHealth ([int]$s.stage_port))) { throw 'Start the stage first.' }
$port = [int]$s.collector_port
if ($port -ne 1088) { throw 'Change both the collector config and launcher together; the supplied config uses 1088.' }
$root = Join-Path $s.runtime_root 'douyin-live'
$exe = Join-Path $root 'douyinLive.exe'
$cfg = Join-Path $root 'config.yaml'
if (-not (Test-Path -LiteralPath $exe)) { throw 'Run Install-DouyinCollector.ps1 first.' }
$ready = $false
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$port/health" -TimeoutSec 2
    $ready = ($health.data.status -eq 'ok' -and $null -ne $health.data.sign_provider)
} catch { }
if (-not $ready) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { throw 'Collector port occupied by another service.' }
    $logs = Join-Path $s.runtime_root 'logs'
    New-Item -ItemType Directory -Path $logs -Force | Out-Null
    Start-Process -FilePath $exe -ArgumentList @('-config',"`"$cfg`"") -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs 'collector.out.log') -RedirectStandardError (Join-Path $logs 'collector.err.log') | Out-Null
    for ($i=0;$i -lt 30;$i++) {
        Start-Sleep -Milliseconds 500
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$port/health" -TimeoutSec 2
            if ($health.data.status -eq 'ok') { $ready=$true; break }
        } catch { }
    }
}
if (-not $ready) { throw 'Collector not ready. Read runtime logs.' }
$python = Join-Path $s.stage_root '.venv\Scripts\python.exe'
$relay = Join-Path $s.stage_root 'tools\douyin_relay.py'
Write-Host '[INFO] Keep this relay window open. Ctrl+C stops forwarding (collector stays in background).'
& $python -u $relay --room $Room --ws-base "ws://127.0.0.1:$port" --bridge "http://127.0.0.1:$($s.stage_port)" --verbose
Assert-Exit 'Danmaku relay'
