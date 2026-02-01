@echo off
echo ========================================
echo HANNA Release Notes PDF Converter
echo ========================================
echo.

cd /d "%~dp0"

REM Check if pandoc is installed
where pandoc >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Pandoc is not installed or not in PATH
    echo.
    echo Please install pandoc from: https://pandoc.org/installing.html
    echo Or add pandoc to your system PATH
    pause
    exit /b 1
)

echo Pandoc found!
echo.

REM Try to convert using LaTeX engine (best quality)
echo Attempting conversion with pdflatex...
pandoc RELEASE_NOTES_v2.0.0.md -o RELEASE_NOTES_v2.0.0.pdf --pdf-engine=pdflatex 2>nul
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS: PDF created with pdflatex!
    goto :success
)

echo pdflatex not available, trying wkhtmltopdf...
pandoc RELEASE_NOTES_v2.0.0.md -o RELEASE_NOTES_v2.0.0.pdf --pdf-engine=wkhtmltopdf 2>nul
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS: PDF created with wkhtmltopdf!
    goto :success
)

echo wkhtmltopdf not available, trying default engine...
pandoc RELEASE_NOTES_v2.0.0.md -o RELEASE_NOTES_v2.0.0.pdf 2>nul
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS: PDF created with default engine!
    goto :success
)

REM If all fail, try converting to HTML first
echo All PDF engines failed, trying HTML conversion...
pandoc RELEASE_NOTES_v2.0.0.md -o RELEASE_NOTES_v2.0.0.html --standalone --self-contained
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS: HTML file created!
    echo You can open RELEASE_NOTES_v2.0.0.html in your browser and print to PDF
    goto :end
)

echo.
echo ERROR: Could not convert the file
echo.
echo Please try one of these alternatives:
echo 1. Install wkhtmltopdf from: https://wkhtmltopdf.org/downloads.html
echo 2. Install MiKTeX (LaTeX) from: https://miktex.org/download
echo 3. Use VS Code extension "Markdown PDF" by yzane
echo 4. Use online converter: https://www.markdowntopdf.com/
goto :end

:success
echo.
echo ========================================
echo PDF Location: %CD%\RELEASE_NOTES_v2.0.0.pdf
echo ========================================
for %%A in ("RELEASE_NOTES_v2.0.0.pdf") do echo File Size: %%~zA bytes
echo.

:end
pause
