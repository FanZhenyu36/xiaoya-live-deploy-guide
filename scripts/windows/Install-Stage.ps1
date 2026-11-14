param([switch]$OriginalUI)
. "$PSScriptRoot\Common.ps1"
$s = Get-GuideSettings
$stage = [IO.Path]::GetFullPath($s.stage_root)
$runtime = [IO.Path]::GetFullPath($s.runtime_root)
$commit = 'c0effaf50d2bbf9dcfde8847a853c5c871d9dee4'
Get-Command git,uv -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Path $runtime -Force | Out-Null
if (-not (Test-Path -LiteralPath (Join-Path $stage '.git'))) {
    if (Test-Path -LiteralPath $stage) { throw "Target exists and is not a Git checkout: $stage" }
    git clone --no-checkout https://github.com/cyber-xiaoya/cyber-xiaoya-live.git $stage
    Assert-Exit 'Clone stage'
    git -C $stage checkout --detach $commit
    Assert-Exit 'Checkout pinned stage'
}
$head = (git -C $stage rev-parse HEAD).Trim()
Assert-Exit 'Read stage revision'
if ($head -ne $commit) { throw 'Unexpected upstream version. Use a new runtime directory; existing files were preserved.' }
$patchNames = @('speech-completion.patch', 'audience-queue.patch')
if (-not $OriginalUI) { $patchNames = @('silver-studio.patch') + $patchNames }
foreach ($patchName in $patchNames) {
    $patch = Join-Path (Join-Path $GuideRoot 'overlays') $patchName
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        git -C $stage apply --reverse --check -- $patch 2>$null
        $alreadyPatched = ($LASTEXITCODE -eq 0)
    } finally { $ErrorActionPreference = $previousPreference }
    if (-not $alreadyPatched) {
        git -C $stage apply --check -- $patch
        Assert-Exit 'Check UI patch (do not overwrite modified files)'
        git -C $stage apply -- $patch
        Assert-Exit 'Apply UI patch'
    }
}
$python = Join-Path $stage '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    uv venv (Join-Path $stage '.venv') --python 3.12
    Assert-Exit 'Create Windows environment'
}
uv pip install --python $python -r (Join-Path $GuideRoot 'requirements\stage-win-py312.lock.txt')
Assert-Exit 'Install stage dependencies'
& $python (Join-Path $GuideRoot 'scripts\configure_stage.py') --stage-root $stage --runtime-root $runtime
Assert-Exit 'Create private configuration'
Write-Host "[OK] Installed in $stage"
Write-Host '[NEXT] Follow README: import a voice, save your API key, then start the stage.'
