@echo off
echo Converting to self-contained HTML...
pandoc docs/releases/RELEASE_NOTES_v2.0.0.md -o docs/releases/RELEASE_NOTES_v2.0.0.html --standalone --self-contained --metadata title="HANNA v2.0.0 Release Notes"
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS! Open docs/releases/RELEASE_NOTES_v2.0.0.html in your browser
    echo Then press Ctrl+P and "Save as PDF"
    start docs/releases/RELEASE_NOTES_v2.0.0.html
) else (
    echo ERROR: Conversion failed
)
pause
