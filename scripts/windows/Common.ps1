$ErrorActionPreference = 'Stop'
$GuideRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
function Get-GuideSettings {
    $path = Join-Path $GuideRoot 'settings.local.json'
    if (-not (Test-Path -LiteralPath $path)) { $path = Join-Path $GuideRoot 'settings.example.json' }
    if ($env:XIAOYA_GUIDE_SETTINGS) { $path = [IO.Path]::GetFullPath($env:XIAOYA_GUIDE_SETTINGS) }
    return (Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json)
}
function Assert-Exit([string]$Label) {
    if ($LASTEXITCODE -ne 0) { throw "$Label failed (exit $LASTEXITCODE)." }
}
function Write-Utf8([string]$Path, [string]$Value) {
    [IO.File]::WriteAllText($Path, $Value, [Text.UTF8Encoding]::new($false))
}
function Test-StageHealth([int]$Port) {
    try {
        $h = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 2
        return ($h.ok -eq $true -and $null -ne $h.build)
    } catch { return $false }
}
function Set-LocalEnvironment {
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
    $bypass = @('localhost','127.0.0.1','::1','0.0.0.0')
    if ($env:NO_PROXY) { $bypass += $env:NO_PROXY.Split(',') }
    if ($env:no_proxy) { $bypass += $env:no_proxy.Split(',') }
    $env:NO_PROXY = ($bypass | Select-Object -Unique) -join ','
}
