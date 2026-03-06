# Hrisa Code Setup Script for Windows (PowerShell)
# Requires PowerShell 5.1+ and Python 3.10+

$ErrorActionPreference = "Stop"

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Hrisa Code - Windows Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check PowerShell version
$psVersion = $PSVersionTable.PSVersion
if ($psVersion.Major -lt 5) {
    Write-Host "ERROR: PowerShell 5.0+ required (you have $psVersion)" -ForegroundColor Red
    Write-Host "Please upgrade PowerShell: https://aka.ms/powershell" -ForegroundColor Yellow
    exit 1
}

Write-Host "PowerShell version: $psVersion" -ForegroundColor Green

# Check Python version
Write-Host ""
Write-Host "Checking Python installation..." -ForegroundColor Cyan

try {
    $pythonVersion = & python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed"
    }

    # Extract version numbers
    if ($pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]

        if (($major -eq 3) -and ($minor -ge 10)) {
            Write-Host "  Python $major.$minor found" -ForegroundColor Green
        } else {
            Write-Host "  ERROR: Python 3.10+ required (found Python $major.$minor)" -ForegroundColor Red
            Write-Host "  Install from: https://www.python.org/downloads/" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "  WARNING: Could not parse Python version" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ERROR: Python not found" -ForegroundColor Red
    Write-Host "  Install from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    exit 1
}

# Check if venv exists
Write-Host ""
Write-Host "Setting up virtual environment..." -ForegroundColor Cyan

$venvPath = "venv"

if (Test-Path $venvPath) {
    Write-Host "  Virtual environment already exists at '$venvPath'" -ForegroundColor Yellow
    $overwrite = Read-Host "  Overwrite? (y/N)"

    if ($overwrite -eq "y" -or $overwrite -eq "Y") {
        Write-Host "  Removing existing venv..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $venvPath
    } else {
        Write-Host "  Using existing venv" -ForegroundColor Green
        $venvPath = $venvPath
    }
}

if (-not (Test-Path $venvPath)) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Cyan
    & python -m venv $venvPath

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }

    Write-Host "  Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Cyan

$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    Write-Host "  ERROR: Activation script not found at $activateScript" -ForegroundColor Red
    exit 1
}

# Execute activation script
& $activateScript

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "  You may need to run: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}

Write-Host "  Virtual environment activated" -ForegroundColor Green

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Cyan
& python -m pip install --upgrade pip --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "  WARNING: Could not upgrade pip" -ForegroundColor Yellow
} else {
    Write-Host "  pip upgraded" -ForegroundColor Green
}

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Cyan
Write-Host "  This may take a few minutes..." -ForegroundColor Yellow

& pip install -e ".[dev]" --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  ERROR: Failed to install dependencies" -ForegroundColor Red
    Write-Host "  Try running manually: pip install -e .[dev]" -ForegroundColor Yellow
    exit 1
}

Write-Host "  Dependencies installed" -ForegroundColor Green

# Check Ollama installation
Write-Host ""
Write-Host "Checking Ollama installation..." -ForegroundColor Cyan

$ollamaPath = Get-Command ollama -ErrorAction SilentlyContinue

if ($ollamaPath) {
    try {
        $ollamaVersion = & ollama --version 2>&1
        Write-Host "  Ollama installed: $ollamaVersion" -ForegroundColor Green

        # Check if Ollama is running
        Write-Host "  Checking Ollama service..." -ForegroundColor Cyan
        $ollamaList = & ollama list 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Ollama service is running" -ForegroundColor Green
        } else {
            Write-Host "  WARNING: Ollama not running" -ForegroundColor Yellow
            Write-Host "  Start Ollama service before using Hrisa Code" -ForegroundColor Yellow
            Write-Host "  Run: ollama serve (in a separate terminal)" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "  WARNING: Ollama found but not responding" -ForegroundColor Yellow
    }
} else {
    Write-Host "  WARNING: Ollama not found" -ForegroundColor Yellow
    Write-Host "  Install from: https://ollama.ai/" -ForegroundColor Cyan
    Write-Host "  Hrisa Code requires Ollama to run local LLMs" -ForegroundColor Yellow
}

# Check Git installation
Write-Host ""
Write-Host "Checking Git installation..." -ForegroundColor Cyan

$gitPath = Get-Command git -ErrorAction SilentlyContinue

if ($gitPath) {
    $gitVersion = & git --version 2>&1
    Write-Host "  Git installed: $gitVersion" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Git not found" -ForegroundColor Yellow
    Write-Host "  Install from: https://git-scm.com/download/windows" -ForegroundColor Cyan
    Write-Host "  Git operations will not be available" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Activate the virtual environment:" -ForegroundColor White
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. Run preflight checks:" -ForegroundColor White
Write-Host "     hrisa check" -ForegroundColor Yellow
Write-Host ""
Write-Host "  3. Initialize configuration:" -ForegroundColor White
Write-Host "     hrisa init" -ForegroundColor Yellow
Write-Host ""
Write-Host "  4. Start the coding assistant:" -ForegroundColor White
Write-Host "     hrisa chat" -ForegroundColor Yellow
Write-Host ""
Write-Host "For help, run: hrisa --help" -ForegroundColor Cyan
Write-Host ""

# Note about execution policy
Write-Host "NOTE: If activation fails, you may need to run:" -ForegroundColor Yellow
Write-Host "  Set-ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Cyan
Write-Host ""
