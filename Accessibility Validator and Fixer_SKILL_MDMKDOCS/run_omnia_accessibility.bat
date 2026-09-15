@echo off
REM Omnia Markdown Accessibility Validator & Fixer - Windows Launcher
REM This script finds Python and runs the accessibility validation script

REM Check if --fix-mode is already provided
set FIX_MODE_PROVIDED=0
for %%a in (%*) do (
    if "%%a"=="--fix-mode" set FIX_MODE_PROVIDED=1
)

REM Default to both mode (auto + interactive) if not provided
REM This automatically fixes simple issues and prompts only for issues requiring human input
if %FIX_MODE_PROVIDED%==0 (
    set ARGS=%* --fix-mode both
) else (
    set ARGS=%*
)

REM Try Python launcher first (installed with Python on Windows)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    py "%~dp0run_omnia_accessibility.py" %ARGS%
    goto :end
)

REM Try python3
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    python3 "%~dp0run_omnia_accessibility.py" %ARGS%
    goto :end
)

REM Try python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python "%~dp0run_omnia_accessibility.py" %ARGS%
    goto :end
)

REM Try common Python installation paths
for %%P in (
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "C:\Python39\python.exe"
    "C:\Python38\python.exe"
    "C:\Python312\python.exe"
    "C:\Program Files\Python311\python.exe"
    "C:\Program Files\Python310\python.exe"
    "C:\Program Files\Python39\python.exe"
    "C:\Program Files\Python38\python.exe"
    "C:\Program Files\Python312\python.exe"
    "C:\Program Files (x86)\Python311\python.exe"
    "C:\Program Files (x86)\Python310\python.exe"
    "C:\Program Files (x86)\Python39\python.exe"
    "C:\Program Files (x86)\Python38\python.exe"
    "C:\Program Files (x86)\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python38\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
) do (
    if exist %%P (
        %%P "%~dp0run_omnia_accessibility.py" %ARGS%
        goto :end
    )
)

echo Error: Python not found. Please install Python from https://python.org
echo Or add Python to your system PATH.
exit /b 1

:end
