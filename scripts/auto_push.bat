@echo off
rem Double-click launcher: starts the auto-push watcher in a visible window.
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\auto_push.ps1" %*
pause
