@echo off
REM ================================================================================
REM OMNIA MARKDOWN ACCESSIBILITY VALIDATOR LAUNCHER
REM ================================================================================
REM This batch script launches the Omnia Markdown Accessibility Validator
REM for checking Markdown/mkdocs documentation for accessibility issues.
REM
REM Usage: run_omnia_md_validator.bat [docs_path] [options]
REM
REM Options:
REM   --no-backup      Skip automatic backup creation
REM   --no-recursive   Don't scan subdirectories recursively
REM
REM Examples:
REM   run_omnia_md_validator.bat ../docs
REM   run_omnia_md_validator.bat ../docs --no-backup
REM   run_omnia_md_validator.bat ../docs --no-recursive
REM ================================================================================

echo ================================================================================
echo OMNIA MARKDOWN ACCESSIBILITY VALIDATOR
echo ================================================================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not available in your environment
    echo Please install Python 3.6 or higher to use this tool
    pause
    exit /b 1
)

REM Set default docs path if not provided
set DOCS_PATH=../docs
if not "%1"=="" set DOCS_PATH=%1

REM Check if the validator script exists
if not exist omnia_md_accessibility_validator.py (
    echo ERROR: omnia_md_accessibility_validator.py not found
    echo Please ensure you are running this script from the correct directory
    pause
    exit /b 1
)

REM Check if the docs directory exists
if not exist "%DOCS_PATH%" (
    echo ERROR: Documentation directory not found: %DOCS_PATH%
    echo Please provide a valid path to your Markdown documentation
    pause
    exit /b 1
)

REM Run the validator with all provided arguments
echo Starting Markdown accessibility validation...
echo Documentation path: %DOCS_PATH%
echo Additional arguments: %2 %3 %4 %5 %6 %7 %8 %9
echo ================================================================================

python omnia_md_accessibility_validator.py "%DOCS_PATH%" %2 %3 %4 %5 %6 %7 %8 %9

if %errorlevel% neq 0 (
    echo ================================================================================
    echo VALIDATION COMPLETED WITH ERRORS
    echo Please review the output above for details
    echo ================================================================================
) else (
    echo ================================================================================
    echo VALIDATION COMPLETED SUCCESSFULLY
    echo Please check the reports directory for generated reports
    echo ================================================================================
)

pause
