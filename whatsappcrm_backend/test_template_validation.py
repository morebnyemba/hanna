#!/usr/bin/env python3
"""
Standalone validation script to test that all fixed templates render correctly.
This can be run without Django setup to quickly validate template changes.
"""
import re
import sys


def validate_template(template_name, template_body):
    """
    Validate that a template doesn't contain problematic patterns.
    Returns (is_valid, issues_list)
    """
    issues = []
    
    # Check for OR expressions
    or_patterns = re.findall(r'\{\{\s*[^}]+\s+or\s+[^}]+\}\}', template_body)
    if or_patterns:
        issues.append(f"OR expressions found: {len(or_patterns)}")
        for pattern in or_patterns[:3]:  # Show first 3
            issues.append(f"  - {pattern}")
    
    # Check for filters
    filters = re.findall(r'\{\{\s*[^}]+\|[^}]+\}\}', template_body)
    if filters:
        issues.append(f"Filters found: {len(filters)}")
        for filt in filters[:3]:  # Show first 3
            issues.append(f"  - {filt}")
    
    # Check for conditionals
    conditionals = re.findall(r'\{%\s*if\s+[^%]+%\}', template_body)
    if conditionals:
        issues.append(f"Conditionals (if blocks) found: {len(conditionals)}")
        for cond in conditionals[:3]:  # Show first 3
            issues.append(f"  - {cond}")
    
    # Check for loops
    loops = re.findall(r'\{%\s*for\s+[^%]+%\}', template_body)
    if loops:
        issues.append(f"Loops (for blocks) found: {len(loops)}")
        for loop in loops[:3]:  # Show first 3
            issues.append(f"  - {loop}")
    
    # Check for nested attributes (multiple dots)
    nested = re.findall(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*\.)', template_body)
    if nested:
        issues.append(f"Nested attributes (multiple dots) found: {len(nested)}")
        for nest in list(set(nested))[:3]:  # Show first 3 unique
            issues.append(f"  - {{{{ {nest}... }}}}")
    
    return len(issues) == 0, issues


def main():
    """Main validation function"""
    
    # Templates that were rejected and need to be validated
    templates_to_validate = [
        'hanna_new_starlink_installation_request',
        'hanna_new_solar_cleaning_request',
        'hanna_new_installation_request',
        'hanna_new_site_assessment_request',
        'hanna_new_placeholder_order_created',
        'hanna_new_order_created',
        'hanna_new_online_order_placed',
        'hanna_admin_order_and_install_created'
    ]
    
    print("=" * 70)
    print("WhatsApp Template Validation")
    print("=" * 70)
    print()
    print("Checking templates for Meta-incompatible patterns...")
    print()
    
    # Read the template definitions file
    try:
        with open('whatsappcrm_backend/flows/management/commands/load_notification_templates.py', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ ERROR: Could not find template definitions file")
        print("   Make sure you're running this from the project root directory")
        return 1
    
    all_valid = True
    results = []
    
    for template_name in templates_to_validate:
        # Find the template in the file
        pattern = f'"name": "{template_name}"[^}}]+?"body": """([^"]+)"""'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            body = match.group(1)
            is_valid, issues = validate_template(template_name, body)
            
            if is_valid:
                results.append((template_name, True, []))
                print(f"✅ {template_name}")
            else:
                results.append((template_name, False, issues))
                all_valid = False
                print(f"❌ {template_name}")
                for issue in issues:
                    print(f"   {issue}")
        else:
            results.append((template_name, False, ["Template not found in file"]))
            all_valid = False
            print(f"⚠️  {template_name}: NOT FOUND")
    
    print()
    print("=" * 70)
    
    if all_valid:
        print("✅ SUCCESS: All templates are Meta-compatible!")
        print()
        print("Next steps:")
        print("1. Run: python manage.py load_notification_templates")
        print("2. Run: python manage.py sync_meta_templates --dry-run")
        print("3. If dry-run looks good: python manage.py sync_meta_templates")
        return 0
    else:
        print("❌ FAILURE: Some templates still have incompatible patterns")
        print()
        print("Templates with issues:")
        for name, is_valid, issues in results:
            if not is_valid:
                print(f"  - {name}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
