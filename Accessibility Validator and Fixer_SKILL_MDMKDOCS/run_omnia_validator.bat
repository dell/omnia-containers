@echo off
setlocal enabledelayedexpansion
REM Omnia Markdown Accessibility Validator - Windows Batch Script
REM Run this script to validate Omnia documentation for accessibility issues
REM Usage: run_omnia_validator.bat [path_to_docs]

echo ================================================================================
echo Omnia Markdown Accessibility Validator
echo ================================================================================
echo.

REM Check if path is provided as command-line argument
if "%~1" neq "" (
    set OMNIA_DOCS_PATH=%~1
    echo Using provided path: %OMNIA_DOCS_PATH%
    echo.
) else (
    REM Check if path is set in environment variable
    if defined OMNIA_DOCS_PATH (
        echo Using path from environment variable: %OMNIA_DOCS_PATH%
        echo.
    ) else (
        REM Prompt user for path
        echo Please enter the path to your documentation directory.
        echo Example: ..\..\2.2.0.0-rc1\omnia-artifactory\docs
        echo Or press Enter to validate current directory.
        echo.
        set /p OMNIA_DOCS_PATH="Enter documentation path (or press Enter for current directory): "
        
        REM If user pressed Enter, use current directory
        if "!OMNIA_DOCS_PATH!"=="" (
            set OMNIA_DOCS_PATH=.
        ) else (
            REM Remove surrounding quotes if present
            set OMNIA_DOCS_PATH=!OMNIA_DOCS_PATH:"=!
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

REM Check if validator script exists
if not exist "omnia_md_accessibility_validator.py" (
    echo ERROR: omnia_md_accessibility_validator.py not found
    echo Please run this script from the skill directory
    pause
    exit /b 1
)

REM Check if documentation path exists
if not exist "%OMNIA_DOCS_PATH%" (
    echo ERROR: Documentation path not found: %OMNIA_DOCS_PATH%
    echo.
    echo Please check the path and try again.
    echo.
    pause
    exit /b 1
)

echo Validating Omnia documentation at: %OMNIA_DOCS_PATH%
echo.

REM Run the validator and generate comprehensive reports
python run_omnia_accessibility.py "%OMNIA_DOCS_PATH%" --validate-only

if errorlevel 1 (
    echo.
    echo ================================================================================
    echo Validation completed with ERRORS found
    echo ================================================================================
    echo Reports saved to: reports/ directory
    echo.
    echo Next steps:
    echo 1. Review COMPREHENSIVE_ACCESSIBILITY_REPORT.txt in reports/
    echo 2. Run the fixer: run_omnia_fixer.bat
    echo 3. Re-validate after fixes
) else (
    echo.
    echo ================================================================================
    echo Validation completed successfully - No errors found
    echo ================================================================================
    echo Reports saved to: reports/ directory
)

echo.
pause
