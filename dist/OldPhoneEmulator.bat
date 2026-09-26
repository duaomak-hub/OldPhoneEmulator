@echo off
REM OldPhoneEmulator Windows Launcher
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found! Install from https://python.org
    pause
    exit /b 1
)
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 pip install flask pillow
if "%1"=="" (
    python "%~dp0OldPhoneEmulator.pyz" --web --port 5000
) else (
    python "%~dp0OldPhoneEmulator.pyz" %*
)
pause
