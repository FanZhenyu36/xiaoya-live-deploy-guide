. "$PSScriptRoot\Common.ps1"
$s = Get-GuideSettings
Set-LocalEnvironment
try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:9877/config' -TimeoutSec 2
    if ($r.StatusCode -eq 200) { Write-Host '[OK] OmniVoice already responds on 9877.'; exit 0 }
} catch { }
$linuxPath = (& wsl.exe -d $s.wsl_distribution -- wslpath -u (Join-Path $GuideRoot 'scripts\wsl\start-omnivoice.sh')).Trim()
Assert-Exit 'Resolve WSL script path'
if (-not $linuxPath) { throw 'Could not resolve path in WSL.' }
Write-Host '[INFO] Model warmup / JIT compilation can take several minutes. Keep this window open.'
& wsl.exe -d $s.wsl_distribution -- bash $linuxPath $s.wsl_home_project
Assert-Exit 'OmniVoice'
