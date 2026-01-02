@echo off
setlocal EnableDelayedExpansion

echo --- Windows Environment Setup ---

where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo uv not found. Installing uv...
    powershell -NoProfile -ExecutionPolicy Bypass ^
        -Command "iwr https://astral.sh/uv/install.ps1 -UseBasicParsing | iex"

    REM Add uv to PATH for this session
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: uv installation failed or PATH not updated.
    exit /b 1
)

echo uv is available.

echo Ensuring Python 3.12 is installed...
uv python install 3.12

if not exist venv (
    echo Creating uv virtual environment...
    uv venv --python 3.12 venv
) else (
    echo venv already exists.
)

if not exist requirements.txt (
    echo ERROR: requirements.txt not found.
    exit /b 1
)

echo Installing dependencies via uv pip...
uv pip install --python venv\Scripts\python.exe -r requirements.txt

echo.
echo --- Windows setup complete ---
echo To activate the environment, run:
echo     venv\Scripts\activate
