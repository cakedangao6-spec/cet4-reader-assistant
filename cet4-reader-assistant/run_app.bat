@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    powershell -ExecutionPolicy Bypass -File ".\install.ps1"
    if errorlevel 1 (
        echo.
        echo Startup failed during installation. Please read the error above.
        pause
        exit /b 1
    )
)

".venv\Scripts\pythonw.exe" -m cet4_reader.main
