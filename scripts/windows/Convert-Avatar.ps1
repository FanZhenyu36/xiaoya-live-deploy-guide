param([Parameter(Mandatory=$true)][string]$InputVideo,[Parameter(Mandatory=$true)][string]$OutputVideo)
. "$PSScriptRoot\Common.ps1"
$source = (Resolve-Path -LiteralPath $InputVideo).Path
$target = [IO.Path]::GetFullPath($OutputVideo)
if ($source -eq $target) { throw 'Input and output must differ.' }
if (Test-Path -LiteralPath $target) { throw 'Output exists; it was preserved.' }
Get-Command ffmpeg -ErrorAction Stop | Out-Null
ffmpeg -hide_banner -nostdin -n -i $source -vf 'fps=15,scale=trunc(iw/2)*2:trunc(ih/2)*2' -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -an $target
Assert-Exit 'Convert avatar'
Write-Host '[OK] New 15fps video created; original preserved. This is for the optional DUIX route.'
