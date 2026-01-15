# Underrail Save Editor - Launch Script (PowerShell)
#
# Usage:
#   .\run.ps1           - Start the interactive console
#   .\run.ps1 view      - View save file data
#   .\run.ps1 edit      - Edit save file
#
# Note: If you get an execution policy error, run:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

$ErrorActionPreference = "Stop"

# Get the script's directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Find Python
$Python = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $null = & $cmd --version 2>&1
        $Python = $cmd
        break
    } catch {
        continue
    }
}

if (-not $Python) {
    Write-Host "Error: Python not found. Please install Python 3."
    exit 1
}

# Run the main screen module
Set-Location $ScriptDir
& $Python -m use.main_screen @args
