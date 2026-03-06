@echo off
REM Hrisa Code Setup Script for Windows (CMD)
REM This is a simple wrapper that calls the PowerShell script

echo ========================================
echo   Hrisa Code - Windows Setup
echo ========================================
echo.
echo This script will run the PowerShell setup script.
echo.
echo If you prefer, you can run the PowerShell script directly:
echo   powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
echo.
pause

REM Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PowerShell not found
    echo Please install PowerShell from: https://aka.ms/powershell
    pause
    exit /b 1
)

REM Run PowerShell script with bypass execution policy
powershell -ExecutionPolicy Bypass -File "%~dp0setup-windows.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Setup failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Setup completed successfully!
pause
