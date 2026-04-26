@echo off
setlocal
cd /d "%~dp0"

echo Starting Family Asset Compass Home v9
echo Current folder: %cd%
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set PY_CMD=py
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set PY_CMD=python
    ) else (
        echo ERROR: Python was not found. Install Python 3.11 or 3.12 and tick Add Python to PATH.
        pause
        exit /b 1
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PY_CMD% -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Launching home assessment tool...
echo If browser does not open, visit http://localhost:8501
".venv\Scripts\python.exe" -m streamlit run app.py
pause
