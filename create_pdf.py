#!/usr/bin/env python3
"""
Simple markdown to PDF converter for HANNA release notes
"""
import subprocess
import sys
import os

def main():
    md_file = "RELEASE_NOTES_v2.0.0.md"
    pdf_file = "RELEASE_NOTES_v2.0.0.pdf"
    
    if not os.path.exists(md_file):
        print(f"ERROR: {md_file} not found")
        return 1
    
    print(f"Converting {md_file} to PDF...")
    print("This may take a moment...")
    
    try:
        # Try using grip (GitHub README Instant Preview) if available
        result = subprocess.run([
            sys.executable, "-m", "grip", 
            md_file, 
            "--export", pdf_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"SUCCESS: Created {pdf_file}")
            return 0
        
        # If grip not available, try markdown-pdf
        print("Trying alternative method...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-q", "markdown-pdf"
        ])
        
        subprocess.check_call([
            "markdown-pdf", md_file, "-o", pdf_file
        ])
        
        print(f"SUCCESS: Created {pdf_file}")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nAlternative: You can convert manually using:")
        print("1. VS Code extension: 'Markdown PDF' by yzane")
        print("2. Online: https://www.markdowntopdf.com/")
        print(f"3. Pandoc: pandoc {md_file} -o {pdf_file}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
