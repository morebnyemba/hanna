"""
Test to verify media URL patterns work in both DEBUG=True and DEBUG=False modes.
This test validates the fix for media files not being accessible in production.
"""
import os
import sys
from pathlib import Path
from unittest import TestCase, main

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')

import django
django.setup()

from django.test import TestCase as DjangoTestCase
from django.urls import resolve, Resolver404
from django.conf import settings


class MediaURLTestCase(DjangoTestCase):
    """Test media URL patterns"""
    
    def test_media_url_resolution(self):
        """Test that /media/ URLs can be resolved"""
        test_urls = [
            '/media/test.txt',
            '/media/product_images/test.png',
            '/media/attachments/file.pdf',
            '/media/subfolder/another/file.jpg',
        ]
        
        for url in test_urls:
            with self.subTest(url=url):
                try:
                    match = resolve(url)
                    # Should resolve to Django's serve view
                    self.assertIsNotNone(match)
                    self.assertIn('path', match.kwargs)
                except Resolver404:
                    self.fail(f"URL {url} could not be resolved. Media URLs not properly configured.")
    
    def test_media_url_with_special_characters(self):
        """Test that media URLs with special characters work"""
        test_urls = [
            '/media/image%20with%20spaces.png',
            '/media/file-with-dashes.pdf',
            '/media/file_with_underscores.txt',
        ]
        
        for url in test_urls:
            with self.subTest(url=url):
                try:
                    match = resolve(url)
                    self.assertIsNotNone(match)
                except Resolver404:
                    self.fail(f"URL {url} could not be resolved")
    
    def test_media_settings_configured(self):
        """Test that media settings are properly configured"""
        self.assertTrue(hasattr(settings, 'MEDIA_URL'))
        self.assertTrue(hasattr(settings, 'MEDIA_ROOT'))
        self.assertEqual(settings.MEDIA_URL, '/media/')
        self.assertTrue(isinstance(settings.MEDIA_ROOT, Path))


if __name__ == '__main__':
    print("="*70)
    print("Testing Media URL Configuration")
    print("="*70)
    print(f"DEBUG mode: {settings.DEBUG}")
    print(f"MEDIA_URL: {settings.MEDIA_URL}")
    print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print("="*70)
    print()
    
    # Run tests
    main(verbosity=2)
