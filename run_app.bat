@echo off
setlocal
cd /d "%~dp0"
echo Checking Python...
where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=py"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python was not found. Install Python from https://www.python.org/downloads/ and try again.
    echo During setup, enable "Add Python to PATH".
    pause
    exit /b 1
  )
  set "PYTHON_CMD=python"
)
echo Installing the app requirements...
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 (
  echo Could not install requirements. Check your internet connection and Python installation.
  pause
  exit /b 1
)
echo Starting ChainCheck in your browser...
%PYTHON_CMD% -m streamlit run streamlit_app.py
if errorlevel 1 pause
