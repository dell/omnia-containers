@echo off
REM ================================================================================
REM OMNIA MARKDOWN ACCESSIBILITY FIXER LAUNCHER
REM ================================================================================
REM This batch script launches the Omnia Markdown Accessibility Fixer
REM for automatically fixing accessibility issues in Markdown/mkdocs documentation.
REM
REM Usage: run_omnia_md_fixer.bat [report_file] [fix_mode]
REM
REM Fix modes:
REM   auto       Run automatic fixes only (default)
REM   interactive Run interactive fixes only
REM   both       Run both automatic and interactive fixes
REM
REM Examples:
REM   run_omnia_md_fixer.bat reports/baseline_validation/accessibility_report.json
REM   run_omnia_md_fixer.bat reports/baseline_validation/accessibility_report.json auto
REM   run_omnia_md_fixer.bat reports/baseline_validation/accessibility_report.json interactive
REM   run_omnia_md_fixer.bat reports/baseline_validation/accessibility_report.json both
REM ================================================================================

echo ================================================================================
echo OMNIA MARKDOWN ACCESSIBILITY FIXER
echo ================================================================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not available in your environment
    echo Please install Python 3.6 or higher to use this tool
    pause
    exit /b 1
)

REM Set default report file if not provided
set REPORT_FILE=reports/baseline_validation/accessibility_report.json
if not "%1"=="" set REPORT_FILE=%1

REM Set default fix mode if not provided
set FIX_MODE=auto
if not "%2"=="" set FIX_MODE=%2

REM Check if the fixer script exists
if not exist omnia_md_accessibility_fixer.py (
    echo ERROR: omnia_md_accessibility_fixer.py not found
    echo Please ensure you are running this script from the correct directory
    pause
    exit /b 1
)

REM Check if the report file exists
if not exist "%REPORT_FILE%" (
    echo ERROR: Report file not found: %REPORT_FILE%
    echo Please provide a valid path to an accessibility report JSON file
    pause
    exit /b 1
)

REM Display fix mode information
echo Fix mode: %FIX_MODE%
if "%FIX_MODE%"=="auto" (
    echo - Automatic fixes only (no user interaction required)
    echo - Fixes insecure links, invalid code languages, and other programmatically resolvable issues
)
if "%FIX_MODE%"=="interactive" (
    echo - Interactive fixes only (requires user input)
    echo - Guides you through fixing issues that require manual intervention
)
if "%FIX_MODE%"=="both" (
    echo - Both automatic and interactive fixes
    echo - Runs automatic fixes first, then guides through manual fixes
)

echo ================================================================================
echo Starting Markdown accessibility fixes...
echo Report file: %REPORT_FILE%
echo ================================================================================

REM Run the fixer with appropriate arguments
if "%FIX_MODE%"=="auto" (
    python omnia_md_accessibility_fixer.py "%REPORT_FILE%" --auto-fix --auto-only
) else if "%FIX_MODE%"=="interactive" (
    python omnia_md_accessibility_fixer.py "%REPORT_FILE%" --interactive
) else if "%FIX_MODE%"=="both" (
    python omnia_md_accessibility_fixer.py "%REPORT_FILE%" --auto-fix
) else (
    echo ERROR: Invalid fix mode: %FIX_MODE%
    echo Valid modes: auto, interactive, both
    pause
    exit /b 1
)

if %errorlevel% neq 0 (
    echo ================================================================================
    echo FIXING COMPLETED WITH ERRORS
    echo Please review the output above for details
    echo ================================================================================
) else (
    echo ================================================================================
    echo FIXING COMPLETED SUCCESSFULLY
    echo Please review the fixed files and re-validate to check remaining issues
    echo ================================================================================
)

pause
