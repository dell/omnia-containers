@echo off
setlocal enabledelayedexpansion
REM Omnia Dual-Mode Accessibility Fixer - Windows Batch Script
REM Run this script to automatically fix accessibility issues
REM Automatically detects and fixes both RST/Sphinx and Markdown/mkdocs files
REM Usage: run_omnia_dual_fixer.bat [report_file_path]

echo ================================================================================
echo Omnia Dual-Mode Accessibility Fixer
echo ================================================================================
echo.

REM Check if report file is provided as command-line argument
if "%~1" neq "" (
    set REPORT_FILE=%~1
    echo Using provided report: %REPORT_FILE%
    echo.
) else (
    REM Check if report file exists in default locations
    if exist "reports\baseline_validation\accessibility_report.json" (
        set REPORT_FILE=reports\baseline_validation\accessibility_report.json
    ) else if exist "accessibility_report.json" (
        set REPORT_FILE=accessibility_report.json
    ) else if exist "omnia_accessibility_report.txt" (
        set REPORT_FILE=omnia_accessibility_report.txt
    ) else (
        REM Prompt user for report file
        echo No accessibility report found in default location.
        echo Please provide the path to your accessibility report file.
        echo Example: reports\baseline_validation\accessibility_report.json
        echo.
        set /p REPORT_FILE="Enter report file path: "
        
        REM If user pressed Enter, show error
        if "!REPORT_FILE!"=="" (
            echo ERROR: No report file provided.
            echo Please run the validator first to generate a report.
            pause
            exit /b 1
        ) else (
            REM Remove surrounding quotes if present
            set REPORT_FILE=!REPORT_FILE:"=!
        )
    )
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.6 or higher from your company portal
    pause
    exit /b 1
)

REM Check if fixer script exists
if not exist "omnia_dual_accessibility_fixer.py" (
    echo ERROR: omnia_dual_accessibility_fixer.py not found
    echo Please run this script from the dual-mode skill directory
    pause
    exit /b 1
)

REM Check if report file exists
if not exist "%REPORT_FILE%" (
    echo ERROR: Report file not found: %REPORT_FILE%
    echo.
    echo Please check the path and try again.
    echo Or run the validator first: run_omnia_dual_validator.bat
    pause
    exit /b 1
)

REM Check if report is text format (fixer needs JSON)
if "%REPORT_FILE%"=="omnia_accessibility_report.txt" (
    echo WARNING: Text report found. The fixer requires JSON format.
    echo The validator now generates JSON by default.
    echo Please delete the old text report and run the validator again.
    echo.
    echo Or manually convert the report to JSON format.
    echo.
    pause
    exit /b 1
)

echo Using report file: %REPORT_FILE%
echo.
echo This fixer will automatically detect and fix:
echo - RST files (.rst) for Sphinx/ReadTheDocs
echo - Markdown files (.md) for mkdocs
echo.

REM Ask user for fix mode
echo Fix Mode Options:
echo 1. Automatic fixes only (recommended first step)
echo 2. Interactive fixes (requires user input for each issue)
echo 3. Both automatic and interactive fixes
echo.
set /p FIX_MODE="Select fix mode (1/2/3): "

if "%FIX_MODE%"=="1" (
    echo.
    echo Applying automatic fixes only...
    python omnia_dual_accessibility_fixer.py "%REPORT_FILE%" --auto-only --backup-dir .omnia_backup
) else if "%FIX_MODE%"=="2" (
    echo.
    echo Applying interactive fixes...
    echo You will be prompted for each issue requiring manual input.
    python omnia_dual_accessibility_fixer.py "%REPORT_FILE%" --interactive --no-auto-fix --backup-dir .omnia_backup
) else if "%FIX_MODE%"=="3" (
    echo.
    echo Applying automatic fixes first, then interactive...
    python omnia_dual_accessibility_fixer.py "%REPORT_FILE%" --interactive --backup-dir .omnia_backup
) else (
    echo Invalid selection. Defaulting to automatic fixes only.
    python omnia_dual_accessibility_fixer.py "%REPORT_FILE%" --auto-only --backup-dir .omnia_backup
)

if errorlevel 1 (
    echo.
    echo ================================================================================
    echo Fixer completed with issues
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo Fixer completed successfully
    echo ================================================================================
)

echo.
echo Next steps:
echo 1. Review the changes in Windsurf/Devin IDE
echo 2. Re-validate: run_omnia_dual_validator.bat [path_to_docs]
echo 3. Commit and push to GitHub
echo 4. Review staging preview (ReadTheDocs or mkdocs)
echo.
echo Backup files saved to: .omnia_backup/
echo.
pause
