@echo off
setlocal
cd /d "%~dp0"
set "PADDLE_PDX_CACHE_HOME=%~dp0data\paddlex_cache"

if not exist ".venv\Scripts\python.exe" (
    call :install_or_pause
    if errorlevel 1 exit /b 1
)

".venv\Scripts\python.exe" -c "import PyQt6" >nul 2>nul
if errorlevel 1 (
    call :install_or_pause
    if errorlevel 1 exit /b 1
)

".venv\Scripts\pythonw.exe" -m cet4_reader.main
exit /b 0

:install_or_pause
powershell -ExecutionPolicy Bypass -File ".\install.ps1"
if errorlevel 1 (
    echo.
    echo Startup failed during installation. Please read the error above.
    pause
    exit /b 1
)
exit /b 0
