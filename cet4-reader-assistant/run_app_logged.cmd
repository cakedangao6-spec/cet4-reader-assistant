@echo off
setlocal
cd /d "%~dp0"

if not exist "runtime" mkdir "runtime"
set "LOG=%~dp0runtime\launcher.log"

echo [%date% %time%] Starting CET-4 Reader>> "%LOG%"

if not exist ".venv\Scripts\python.exe" (
    powershell -ExecutionPolicy Bypass -File ".\install.ps1" >> "%LOG%" 2>&1
    if errorlevel 1 (
        echo [%date% %time%] Install failed.>> "%LOG%"
        exit /b 1
    )
)

".venv\Scripts\python.exe" -m cet4_reader.main >> "%LOG%" 2>&1
exit /b %errorlevel%
