. "$PSScriptRoot\Common.ps1"
$s=Get-GuideSettings
$root=[IO.Path]::GetFullPath($s.stage_root)
$path=Join-Path $root 'config.json'
if(-not (Test-Path -LiteralPath $path)){return}
$conf=Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
if(-not $conf.stt.python_exe -or -not $conf.stt.model_dir){return}
try{$h=Invoke-RestMethod http://127.0.0.1:8798/health -TimeoutSec 2;if($h.kind -eq 'xiaoya-local-asr'){return}}catch{}
if(Get-NetTCPConnection -State Listen -LocalPort 8798 -ErrorAction SilentlyContinue){throw 'ASR port 8798 is occupied.'}
$decoder=$conf.stt.ffmpeg
if(-not $decoder){$decoder=(Get-Command ffmpeg -ErrorAction Stop).Source}
$worker=Join-Path $root 'src\stt_worker.py'
$logs=Join-Path $s.runtime_root 'logs'
New-Item -ItemType Directory -Path $logs -Force | Out-Null
Set-LocalEnvironment
Start-Process -FilePath $conf.stt.python_exe -ArgumentList @('-u',"`"$worker`"",'--model',"`"$($conf.stt.model_dir)`"",'--ffmpeg',"`"$decoder`"") -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs 'stt.out.log') -RedirectStandardError (Join-Path $logs 'stt.err.log') | Out-Null
for($i=0;$i -lt 30;$i++){
    Start-Sleep -Milliseconds 500
    try{$h=Invoke-RestMethod http://127.0.0.1:8798/health -TimeoutSec 2;if($h.kind -eq 'xiaoya-local-asr'){Write-Host '[OK] Local ASR ready.';return}}catch{}
}
throw 'Local ASR startup failed. Check stt.err.log.'
