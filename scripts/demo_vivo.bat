@echo off
rem Doble clic: abre la demostracion en vivo (Windows Terminal si existe; si no, una consola PowerShell). No modifica datos protegidos.
cd /d "%~dp0.."
where wt >nul 2>nul
if %errorlevel%==0 (
    start "MPSR demo" wt -d "%CD%" powershell -NoExit -ExecutionPolicy Bypass -File "%CD%\scripts\demo_vivo.ps1" %*
) else (
    start "MPSR demo" powershell -NoExit -ExecutionPolicy Bypass -File "%CD%\scripts\demo_vivo.ps1" %*
)
