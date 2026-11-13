. "$PSScriptRoot\Common.ps1"
$s = Get-GuideSettings
Set-LocalEnvironment
foreach ($name in @('git','uv','python','ffmpeg','wsl.exe','nvidia-smi')) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { Write-Host "[OK] $name : $($cmd.Source)" } else { Write-Host "[MISSING] $name" -ForegroundColor Yellow }
}
foreach ($item in @(@{port=9877;path='/config'},@{port=[int]$s.stage_port;path='/api/health'},@{port=[int]$s.collector_port;path='/health'})) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$($item.port)$($item.path)" -TimeoutSec 3
        Write-Host "[OK] HTTP $($r.StatusCode) on port $($item.port)"
    } catch { Write-Host "[OFFLINE] port $($item.port) (optional services may be off)" }
}
Write-Host '[INFO] This diagnostic does not start models, create a live, or print API keys.'
