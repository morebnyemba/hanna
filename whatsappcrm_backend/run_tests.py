#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'whatsappcrm_backend.settings'
    
    # Import and update settings before Django setup
    from django.conf import settings
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
    
    django.setup()
    
    # Create test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)
    
    # Run tests
    failures = test_runner.run_tests(["products_and_services.tests.ProductMetaCatalogSyncTestCase"])
    
    sys.exit(bool(failures))
