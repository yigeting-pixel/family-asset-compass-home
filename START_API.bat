@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    py -m venv .venv
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
echo Starting API at http://127.0.0.1:8000/docs
".venv\Scripts\python.exe" -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
pause
