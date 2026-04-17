@echo off
REM DocRAG Search — one-click launcher (Windows)

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python run.py %*
