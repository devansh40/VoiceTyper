$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

if (-not (Test-Path ".venv")) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -m venv .venv
    } else {
        python -m venv .venv
    }
}

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. "$scriptDir\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
