. "$PSScriptRoot\Common.ps1"
$s = Get-GuideSettings
if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { throw 'This pinned download is Windows x64 only.' }
$root = Join-Path $s.runtime_root 'douyin-live'
$exe = Join-Path $root 'douyinLive.exe'
if (Test-Path -LiteralPath $exe) { Write-Host '[SKIP] Collector already exists. Existing config preserved.'; exit 0 }
$url = 'https://github.com/jwwsjlm/douyinLive/releases/download/v2.3.2/douyinLive-v2.3.2-3b0c44876c2a-windows-amd64.zip'
$expected = 'da050a808fe468e7d4702175bab6dd8a46565c7a38eb923c143c8797b5157375'
New-Item -ItemType Directory -Path $root -Force | Out-Null
$zip = Join-Path $root 'collector-download.zip'
Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $zip -TimeoutSec 180
$actual = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw 'Checksum mismatch. Archive was not extracted or executed.' }
$unpack = Join-Path $root 'release'
Expand-Archive -LiteralPath $zip -DestinationPath $unpack -Force
$found = @(Get-ChildItem -LiteralPath $unpack -Filter douyinLive.exe -Recurse -File)
if ($found.Count -ne 1) { throw 'Unexpected release layout.' }
Copy-Item -LiteralPath $found[0].FullName -Destination $exe
$cfg = Join-Path $root 'config.yaml'
if (-not (Test-Path -LiteralPath $cfg)) { Copy-Item -LiteralPath (Join-Path $GuideRoot 'config\douyin.example.yaml') -Destination $cfg }
Write-Host '[OK] Official release downloaded and SHA256 verified. It has not been executed.'
Write-Host '[NEXT] Read docs/07-douyin-obs.md before starting.'
