"""
Convert docs/releases/RELEASE_NOTES_v2.0.0.md to PDF
Uses markdown2 and weasyprint for conversion
"""

import os
import sys

try:
    import markdown2
    import weasyprint
    print("✓ Dependencies found")
except ImportError as e:
    print(f"Missing dependencies. Installing...")
    os.system(f"{sys.executable} -m pip install markdown2 weasyprint")
    import markdown2
    import weasyprint

def convert_md_to_pdf(md_file, pdf_file):
    """Convert markdown file to PDF"""
    
    # Read markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown2.markdown(md_content, extras=[
        'tables',
        'fenced-code-blocks',
        'header-ids',
        'strike',
        'task_list'
    ])
    
    # Add CSS styling for better PDF formatting
    html_with_style = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 100%;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                font-size: 28px;
                margin-top: 30px;
            }}
            h2 {{
                color: #2980b9;
                border-bottom: 2px solid #3498db;
                padding-bottom: 8px;
                font-size: 24px;
                margin-top: 25px;
            }}
            h3 {{
                color: #3498db;
                font-size: 20px;
                margin-top: 20px;
            }}
            h4 {{
                color: #5dade2;
                font-size: 18px;
                margin-top: 15px;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
            }}
            pre {{
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-left: 3px solid #3498db;
                padding: 15px;
                overflow-x: auto;
                border-radius: 5px;
            }}
            pre code {{
                background-color: transparent;
                padding: 0;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                font-size: 14px;
            }}
            th {{
                background-color: #3498db;
                color: white;
                padding: 12px;
                text-align: left;
                border: 1px solid #2980b9;
            }}
            td {{
                padding: 10px;
                border: 1px solid #ddd;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            ul, ol {{
                margin: 10px 0;
                padding-left: 30px;
            }}
            li {{
                margin: 5px 0;
            }}
            blockquote {{
                border-left: 4px solid #3498db;
                padding-left: 15px;
                margin-left: 0;
                color: #666;
                font-style: italic;
            }}
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            .emoji {{
                font-size: 1.2em;
            }}
            hr {{
                border: none;
                border-top: 2px solid #3498db;
                margin: 30px 0;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert HTML to PDF
    print(f"Converting {md_file} to {pdf_file}...")
    weasyprint.HTML(string=html_with_style).write_pdf(pdf_file)
    print(f"✓ PDF created successfully: {pdf_file}")
    print(f"  File size: {os.path.getsize(pdf_file) / 1024:.2f} KB")

if __name__ == "__main__":
    md_file = "docs/releases/RELEASE_NOTES_v2.0.0.md"
    pdf_file = "docs/releases/RELEASE_NOTES_v2.0.0.pdf"
    
    if not os.path.exists(md_file):
        print(f"Error: {md_file} not found!")
        sys.exit(1)
    
    try:
        convert_md_to_pdf(md_file, pdf_file)
        print("\n✅ Conversion complete!")
        print(f"📄 PDF file: {os.path.abspath(pdf_file)}")
    except Exception as e:
        print(f"\n❌ Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
