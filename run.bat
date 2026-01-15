@echo off
REM Underrail Save Editor - Launch Script (Windows)
REM
REM Usage:
REM   run.bat           - Start the interactive console
REM   run.bat view      - View save file data
REM   run.bat edit      - Edit save file

setlocal

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Try to find Python
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON=python"
    goto :run
)

where python3 >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON=python3"
    goto :run
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON=py -3"
    goto :run
)

echo Error: Python not found. Please install Python 3.
exit /b 1

:run
cd /d "%SCRIPT_DIR%"
%PYTHON% -m use.main_screen %*
