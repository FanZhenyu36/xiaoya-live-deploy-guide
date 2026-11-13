@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows\Start-Stage.ps1"
if errorlevel 1 pause
