from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Retailer(models.Model):
    """
    Represents a retailer company that can have multiple branches.
    Retailer accounts can only manage branches - they cannot perform 
    check-in/checkout operations directly.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='retailer_profile',
        help_text=_("The user account associated with this retailer.")
    )
    company_name = models.CharField(
        _("Company Name"),
        max_length=255,
        help_text=_("The name of the retailer's business.")
    )
    business_registration_number = models.CharField(
        _("Business Registration Number"),
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text=_("Official business registration number.")
    )
    contact_phone = models.CharField(
        _("Contact Phone"),
        max_length=20,
        blank=True,
        null=True,
        help_text=_("Primary contact phone number.")
    )
    address = models.TextField(
        _("Address"),
        blank=True,
        null=True,
        help_text=_("Business address of the retailer's headquarters.")
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether this retailer account is active.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} ({self.user.username})"

    class Meta:
        verbose_name = _("Retailer")
        verbose_name_plural = _("Retailers")
        ordering = ['company_name']


class RetailerBranch(models.Model):
    """
    Represents a branch of a retailer. Each branch has its own user account
    and can perform check-in/checkout operations on products.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='retailer_branch_profile',
        help_text=_("The user account for this branch to login.")
    )
    retailer = models.ForeignKey(
        Retailer,
        on_delete=models.CASCADE,
        related_name='branches',
        help_text=_("The parent retailer this branch belongs to.")
    )
    branch_name = models.CharField(
        _("Branch Name"),
        max_length=255,
        help_text=_("Name or identifier for this branch location.")
    )
    branch_code = models.CharField(
        _("Branch Code"),
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Internal code for this branch.")
    )
    contact_phone = models.CharField(
        _("Contact Phone"),
        max_length=20,
        blank=True,
        null=True,
        help_text=_("Branch contact phone number.")
    )
    address = models.TextField(
        _("Address"),
        blank=True,
        null=True,
        help_text=_("Physical address of this branch.")
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether this branch is active.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.branch_name} - {self.retailer.company_name}"

    class Meta:
        verbose_name = _("Retailer Branch")
        verbose_name_plural = _("Retailer Branches")
        ordering = ['retailer', 'branch_name']
        unique_together = [['retailer', 'branch_name']]
