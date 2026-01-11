#!/bin/bash

# QUICKSTART - Create GitHub Issues for HANNA
# This script provides the fastest way to create all issues

echo "🚀 HANNA Issue Creation Quick Start"
echo "===================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."
echo ""

# Check gh CLI
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo "   Install from: https://cli.github.com/"
    exit 1
fi
echo "✓ GitHub CLI found"

# Check authentication
if ! gh auth status &>/dev/null; then
    echo "⚠️  GitHub CLI is not authenticated"
    echo ""
    echo "Please authenticate now:"
    gh auth login
    
    if ! gh auth status &>/dev/null; then
        echo "❌ Authentication failed"
        exit 1
    fi
fi
echo "✓ GitHub CLI authenticated"
echo ""

# Confirm action
echo "This script will create 7 GitHub issues in morebnyemba/hanna"
echo ""
read -p "Do you want to continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Creating issues..."
echo "===================="
echo ""

# Run the main creation script
./create_issues.sh

echo ""
echo "✅ Done!"
echo ""
echo "Next steps:"
echo "1. Review the created issues on GitHub"
echo "2. Assign GitHub Copilot to issues you want automated"
echo "3. Set up a project board to track progress"
echo "4. Begin implementation following the recommended order"
echo ""
echo "For more details, see:"
echo "- CREATE_ISSUES_GUIDE.md"
echo "- ISSUE_CREATION_SUMMARY.md"
echo ""
