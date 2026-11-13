param([Parameter(Mandatory=$true)][string]$Audio,[Parameter(Mandatory=$true)][string]$TextFile,[string]$Name='my_voice')
. "$PSScriptRoot\Common.ps1"
$s = Get-GuideSettings
if ($Name -notmatch '^[A-Za-z0-9_-]+$') { throw 'Voice name must use letters, numbers, underscores or hyphens.' }
$source = (Resolve-Path -LiteralPath $Audio).Path
$text = (Resolve-Path -LiteralPath $TextFile).Path
$target = Join-Path (Join-Path $s.runtime_root 'voices') $Name
if (Test-Path -LiteralPath $target) { throw 'Voice already exists. Choose another name; existing voice was preserved.' }
Get-Command ffmpeg -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Path $target -Force | Out-Null
ffmpeg -hide_banner -loglevel error -nostdin -n -i $source -ac 1 -ar 16000 -c:a pcm_s16le (Join-Path $target 'ref_audio.wav')
Assert-Exit 'Convert reference audio'
Write-Utf8 (Join-Path $target 'ref_text.txt') ([IO.File]::ReadAllText($text,[Text.Encoding]::UTF8).Trim())
Write-Utf8 (Join-Path $target 'omnivoice.txt') 'OmniVoice voice cloning preset'
Write-Host "[OK] Voice imported: $Name. Select it from the stage voice menu."
