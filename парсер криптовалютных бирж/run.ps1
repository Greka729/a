$ErrorActionPreference = 'Stop'

$python = 'python'
try {
  & $python --version | Out-Null
} catch {
  Write-Error 'Python is not installed or not on PATH.'
  exit 1
}

if (-not (Test-Path -Path ".venv")) {
  Write-Host 'Creating virtual environment (.venv)...'
  & $python -m venv .venv
}

$venvActivate = Join-Path ".venv" "Scripts\Activate.ps1"
. $venvActivate

pip install --upgrade pip
if (Test-Path -Path "requirements.txt") {
  pip install -r requirements.txt
}

$env:PYTHONPATH = "$PWD"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
