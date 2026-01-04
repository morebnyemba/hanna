"""
Models for third-party integrations.
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from typing import Optional
from datetime import datetime


class ZohoCredential(models.Model):
    """
    Singleton model to store Zoho API credentials and tokens.
    Only one instance should exist in the database.
    """
    client_id = models.CharField(
        _("Client ID"),
        max_length=255,
        help_text=_("Zoho OAuth Client ID")
    )
    client_secret = models.CharField(
        _("Client Secret"),
        max_length=255,
        help_text=_("Zoho OAuth Client Secret")
    )
    access_token = models.TextField(
        _("Access Token"),
        blank=True,
        null=True,
        help_text=_("Current OAuth access token")
    )
    refresh_token = models.TextField(
        _("Refresh Token"),
        blank=True,
        null=True,
        help_text=_("OAuth refresh token for obtaining new access tokens")
    )
    expires_in = models.DateTimeField(
        _("Token Expiration"),
        blank=True,
        null=True,
        help_text=_("When the current access token expires")
    )
    scope = models.CharField(
        _("Scope"),
        max_length=500,
        blank=True,
        default="ZohoInventory.items.READ",
        help_text=_("OAuth scope permissions")
    )
    organization_id = models.CharField(
        _("Organization ID"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Zoho organization/company ID")
    )
    api_domain = models.CharField(
        _("API Domain"),
        max_length=255,
        default="https://inventory.zohoapis.com",
        help_text=_("Zoho API domain (e.g., https://inventory.zohoapis.com, https://inventory.zohoapis.eu)")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Zoho Credential")
        verbose_name_plural = _("Zoho Credentials")

    def __str__(self) -> str:
        return f"Zoho Credentials (Client ID: {self.client_id[:10]}...)"

    def save(self, *args, **kwargs):
        """
        Ensure only one instance exists (singleton pattern).
        """
        if not self.pk and ZohoCredential.objects.exists():
            # If trying to create a new instance when one already exists,
            # update the existing one instead
            existing = ZohoCredential.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls) -> Optional['ZohoCredential']:
        """
        Get the singleton instance of ZohoCredential.
        Returns None if not configured yet.
        """
        return cls.objects.first()

    def is_expired(self) -> bool:
        """
        Check if the current access token has expired.
        
        Returns:
            bool: True if token is expired or not set, False otherwise
        """
        if not self.access_token or not self.expires_in:
            return True
        
        # Add a 5-minute buffer to refresh before actual expiration
        buffer_time = timezone.timedelta(minutes=5)
        return timezone.now() >= (self.expires_in - buffer_time)


class OAuthState(models.Model):
    """
    Model to store OAuth state tokens for CSRF protection.
    Tokens expire after 10 minutes and are one-time use.
    """
    state = models.CharField(
        _("State Token"),
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_("OAuth state token for CSRF protection")
    )
    user_id = models.IntegerField(
        _("User ID"),
        blank=True,
        null=True,
        help_text=_("ID of the user who initiated the OAuth flow")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(
        _("Used"),
        default=False,
        help_text=_("Whether this state token has been used")
    )
    
    class Meta:
        verbose_name = _("OAuth State")
        verbose_name_plural = _("OAuth States")
        indexes = [
            models.Index(fields=['state', 'used']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self) -> str:
        return f"OAuth State: {self.state[:10]}... (Used: {self.used})"
    
    def is_valid(self) -> bool:
        """
        Check if the state token is valid (not used and not expired).
        
        Returns:
            bool: True if valid, False otherwise
        """
        if self.used:
            return False
        
        # Check if not too old (max 10 minutes)
        cutoff_time = timezone.now() - timezone.timedelta(minutes=10)
        return self.created_at >= cutoff_time
    
    def mark_as_used(self) -> None:
        """Mark this state token as used."""
        self.used = True
        self.save(update_fields=['used'])
    
    @classmethod
    def cleanup_expired(cls) -> int:
        """
        Remove expired state tokens (older than 10 minutes).
        
        Returns:
            int: Number of tokens deleted
        """
        cutoff_time = timezone.now() - timezone.timedelta(minutes=10)
        count, _ = cls.objects.filter(created_at__lt=cutoff_time).delete()
        return count
