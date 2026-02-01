@echo off
echo Converting to self-contained HTML...
pandoc RELEASE_NOTES_v2.0.0.md -o RELEASE_NOTES_v2.0.0.html --standalone --self-contained --metadata title="HANNA v2.0.0 Release Notes"
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS! Open RELEASE_NOTES_v2.0.0.html in your browser
    echo Then press Ctrl+P and "Save as PDF"
    start RELEASE_NOTES_v2.0.0.html
) else (
    echo ERROR: Conversion failed
)
pause
