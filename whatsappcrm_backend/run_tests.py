#!/usr/bin/env python
"""
Test runner for the WhatsApp CRM backend.
Uses SQLite in-memory database for isolated testing without external dependencies.

Usage:
    python run_tests.py                              # Run default test suite
    python run_tests.py app.tests                    # Run specific app tests
    python run_tests.py app.tests.TestCase           # Run specific test case
    python run_tests.py app.tests.TestCase.test_name # Run specific test
"""
import os
import sys

# Set environment variables before importing Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.test_settings')

import django
django.setup()

from django.test.utils import get_runner
from django.conf import settings

if __name__ == "__main__":
    # Create test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False)
    
    # Run tests - allow specifying test modules via command line args
    test_labels = sys.argv[1:] if len(sys.argv) > 1 else ["products_and_services.tests.ProductMetaCatalogSyncTestCase"]
    failures = test_runner.run_tests(test_labels)
    
    sys.exit(bool(failures))
