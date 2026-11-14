param([switch]$NoBrowser, [switch]$Foreground)
. "$PSScriptRoot\Common.ps1"
$s = Get-GuideSettings
Set-LocalEnvironment
$stage = [IO.Path]::GetFullPath($s.stage_root)
& "$PSScriptRoot\Start-ASR.ps1"
$python = Join-Path $stage '.venv\Scripts\python.exe'
$port = [int]$s.stage_port
$url = "http://127.0.0.1:$port/stage"
if (Test-StageHealth $port) {
    Write-Host "[OK] A compatible stage already responds at $url. Reusing it."
    if (-not $NoBrowser) { Start-Process $url }
    exit 0
}
if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
    throw "Port $port belongs to another process. Nothing was stopped."
}
if (-not (Test-Path -LiteralPath $python)) { throw 'Run Install-Stage.ps1 first.' }
if (-not (Test-Path -LiteralPath (Join-Path $stage 'config.json'))) { throw 'Missing config.json.' }
Get-Command ffmpeg -ErrorAction Stop | Out-Null
if ($Foreground) {
    Push-Location $stage
    try { & $python -u -m src.main --host 127.0.0.1 --port $port --no-browser; Assert-Exit 'Stage' }
    finally { Pop-Location }
    exit 0
}
$logs = Join-Path $s.runtime_root 'logs'
New-Item -ItemType Directory -Path $logs -Force | Out-Null
$p = Start-Process -FilePath $python -ArgumentList @('-u','-m','src.main','--host','127.0.0.1','--port',"$port",'--no-browser') -WorkingDirectory $stage -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logs 'stage.out.log') -RedirectStandardError (Join-Path $logs 'stage.err.log')
Write-Utf8 (Join-Path $s.runtime_root 'stage-process.json') (@{pid=$p.Id; python=$python; stage=$stage; started=$p.StartTime.ToUniversalTime().ToString('o')} | ConvertTo-Json)
for ($i=0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-StageHealth $port) {
        Write-Host "[OK] $url"
        if (-not $NoBrowser) { Start-Process $url }
        exit 0
    }
}
throw "Stage not ready. Read $logs\stage.err.log (no process was force-stopped)."
