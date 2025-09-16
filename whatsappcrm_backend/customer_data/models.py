# whatsappcrm_backend/customer_data/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _ # type: ignore
from django.conf import settings
from django.utils import timezone
from conversations.models import Contact
import uuid

class LeadStatus(models.TextChoices):
    """Defines the choices for the lead status in the sales pipeline."""
    NEW = 'new', _('New')
    CONTACTED = 'contacted', _('Contacted')
    QUALIFIED = 'qualified', _('Qualified')
    PROPOSAL_SENT = 'proposal_sent', _('Proposal Sent')
    NEGOTIATION = 'negotiation', _('Negotiation')
    WON = 'won', _('Won')
    LOST = 'lost', _('Lost')
    ON_HOLD = 'on_hold', _('On Hold')

class InteractionType(models.TextChoices):
    """Defines the types of interactions that can be logged."""
    CALL = 'call', _('Call')
    EMAIL = 'email', _('Email')
    WHATSAPP = 'whatsapp', _('WhatsApp Message')
    MEETING = 'meeting', _('Meeting')
    NOTE = 'note', _('Internal Note')
    OTHER = 'other', _('Other')

class CustomerProfile(models.Model):
    """
    Stores aggregated and specific data about a customer, linked to their Contact record.
    This profile is enriched over time through conversations, forms, and manual entry.
    """
    contact = models.OneToOneField(
        Contact,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        primary_key=True,
        help_text=_("The contact this customer profile belongs to.")
    )
    
    # Basic Info (can be synced or enriched)
    first_name = models.CharField(_("First Name"), max_length=100, blank=True, null=True)
    last_name = models.CharField(_("Last Name"), max_length=100, blank=True, null=True)
    email = models.EmailField(_("Email Address"), max_length=254, blank=True, null=True)
    company = models.CharField(_("Company"), max_length=150, blank=True, null=True)
    role = models.CharField(_("Role/Title"), max_length=100, blank=True, null=True)
    
    # Location Details
    address_line_1 = models.CharField(_("Address Line 1"), max_length=255, blank=True, null=True)
    address_line_2 = models.CharField(_("Address Line 2"), max_length=255, blank=True, null=True)
    city = models.CharField(_("City"), max_length=100, blank=True, null=True)
    state_province = models.CharField(_("State/Province"), max_length=100, blank=True, null=True)
    postal_code = models.CharField(_("Postal Code"), max_length=20, blank=True, null=True)
    country = models.CharField(_("Country"), max_length=100, blank=True, null=True)
    
    # Sales & Lead Information
    lead_status = models.CharField(
        _("Lead Status"),
        max_length=50,
        choices=LeadStatus.choices,
        default=LeadStatus.NEW,
        db_index=True,
        help_text=_("The current stage of the customer in the sales pipeline.")
    )
    potential_value = models.DecimalField(
        _("Potential Value"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Estimated value of the deal or lifetime value of the customer.")
    )
    acquisition_source = models.CharField(
        _("Acquisition Source"),
        max_length=150, 
        blank=True, 
        null=True, 
        help_text=_("How this customer was acquired, e.g., 'Website Form', 'Cold Call', 'Referral'")
    )
    lead_score = models.IntegerField(
        _("Lead Score"),
        default=0,
        db_index=True,
        help_text=_("A score to qualify leads, can be updated by flow actions.")
    )
    
    # Agent Assignment & Segmentation
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name='assigned_customers',
        help_text=_("The sales or support agent assigned to this customer.")
    )
    tags = models.JSONField(
        _("Tags"),
        default=list, 
        blank=True, 
        help_text=_("Descriptive tags for segmentation, e.g., ['high-priority', 'tech-industry', 'follow-up']")
    )
    
    # Notes & Custom Data
    notes = models.TextField(
        _("Notes"), 
        blank=True, 
        null=True,
        help_text=_("General notes about the customer, their needs, or past interactions.")
    )
    custom_attributes = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Flexible field for storing custom data collected via forms or integrations.")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_interaction_date = models.DateTimeField(
        _("Last Interaction Date"),
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Timestamp of the last recorded interaction with this customer.")
    )

    def get_full_name(self) -> str | None:
        """Returns the full name of the customer, or None if no name is set."""
        parts = [self.first_name, self.last_name]
        full_name = " ".join(p for p in parts if p)
        return full_name or None

    def __str__(self) -> str:
        """Returns a string representation of the customer profile."""
        display_name = self.get_full_name() or self.contact.name or self.contact.whatsapp_id
        return f"Customer: {display_name}"

    class Meta:
        verbose_name = _("Customer Profile")
        verbose_name_plural = _("Customer Profiles")
        ordering = ['-last_interaction_date', '-updated_at']


class Interaction(models.Model):
    """
    Represents a single interaction with a customer, such as a call, email, or meeting.
    This creates a historical log of all communications.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name='interactions',
        help_text=_("The customer this interaction is associated with.")
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interactions',
        help_text=_("The agent who had the interaction.")
    )
    interaction_type = models.CharField(
        _("Interaction Type"),
        max_length=50,
        choices=InteractionType.choices,
        default=InteractionType.NOTE
    )
    notes = models.TextField(
        _("Notes / Summary"),
        help_text=_("A summary of the interaction, key points, and next steps.")
    )
    created_at = models.DateTimeField(
        _("Interaction Time"),
        default=timezone.now,
        help_text=_("When the interaction occurred.")
    )

    def __str__(self) -> str:
        """Returns a string representation of the interaction."""
        return f"{self.get_interaction_type_display()} with {self.customer} on {self.created_at.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs) -> None:
        """
        Overrides the save method to automatically update the related customer's
        `last_interaction_date` field. This ensures the customer profile
        always reflects the latest activity.
        """
        super().save(*args, **kwargs)
        if self.customer:
            # Using update_fields is a performance best practice, as it avoids
            # re-saving all fields and triggering unnecessary database operations.
            self.customer.last_interaction_date = self.created_at
            self.customer.save(update_fields=['last_interaction_date']) # type: ignore

    class Meta:
        verbose_name = _("Interaction")
        verbose_name_plural = _("Interactions")
        ordering = ['-created_at']


class Order(models.Model):
    """
    Represents a sales order with a customer, linking them to
    specific products or services via OrderItems.
    """
    class Stage(models.TextChoices):
        PROSPECTING = 'prospecting', _('Prospecting')
        QUALIFICATION = 'qualification', _('Qualification')
        PROPOSAL = 'proposal', _('Proposal')
        NEGOTIATION = 'negotiation', _('Negotiation')
        CLOSED_WON = 'closed_won', _('Closed Won')
        CLOSED_LOST = 'closed_lost', _('Closed Lost')

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending Payment')
        PAID = 'paid', _('Paid')
        PARTIALLY_PAID = 'partially_paid', _('Partially Paid')
        REFUNDED = 'refunded', _('Refunded')
        NOT_APPLICABLE = 'not_applicable', _('Not Applicable')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(_("Order Number"), max_length=100, unique=True, blank=True, null=True, help_text=_("Unique order number or reference for this order."))
    name = models.CharField(_("Order Name"), max_length=255, help_text=_("e.g., '5kVA Solar Kit for Mr. Smith'"))
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    stage = models.CharField(
        _("Stage"),
        max_length=50,
        choices=Stage.choices,
        default=Stage.PROSPECTING,
        db_index=True
    )
    payment_status = models.CharField(
        _("Payment Status"),
        max_length=50,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    amount = models.DecimalField(_("Amount"), max_digits=12, decimal_places=2, help_text=_("The estimated or actual value of the deal."))
    currency = models.CharField(_("Currency"), max_length=3, default='USD')
    expected_close_date = models.DateField(_("Expected Close Date"), null=True, blank=True)
    
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.order_number or self.id} for {self.customer}"

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ['-updated_at']


class OrderItem(models.Model):
    """
    Represents a line item within an Order, linking a specific
    product with a quantity and price.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'products_and_services.Product', 
        on_delete=models.PROTECT, # Don't allow deleting a product that's in an order
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    unit_price = models.DecimalField(
        _("Unit Price"), max_digits=12, decimal_places=2,
        help_text=_("Price of the product at the time the order was placed.")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} for Order {self.order.id}"



class PaymentStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    SUCCESSFUL = 'successful', _('Successful')
    FAILED = 'failed', _('Failed')
    CANCELLED = 'cancelled', _('Cancelled')
    AWAITING_DELIVERY = 'awaiting_delivery', _('Awaiting Delivery')
    DELIVERED = 'delivered', _('Delivered')


class Payment(models.Model):
    """
    Represents a payment transaction, typically initiated through a flow
    and processed by a payment gateway like Paynow.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        help_text=_("The customer who made the payment.")
    )
    order = models.ForeignKey(
        'Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        help_text=_("The sales order this payment is for.")
    )
    amount = models.DecimalField(_("Amount"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=3, default='USD')
    status = models.CharField(
        _("Payment Status"), max_length=50, choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING, db_index=True
    )
    payment_method = models.CharField(_("Payment Method"), max_length=50, default='paynow')
    provider_transaction_id = models.CharField(
        _("Provider Transaction ID"), max_length=255, blank=True, null=True, db_index=True,
        help_text=_("The unique ID for this transaction from the payment provider (e.g., Paynow poll URL or reference).")
    )
    poll_url = models.CharField(
        _("Paynow Poll URL"), max_length=255, blank=True, null=True,
        help_text=_("The URL to poll for transaction status updates from Paynow.")
    )
    provider_response = models.JSONField(
        _("Provider Response"), default=dict, blank=True,
        help_text=_("The last raw response received from the payment provider.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id} for {self.customer} - {self.amount} {self.currency} ({self.get_status_display()})"

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ['-created_at']


class InstallationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    INSTALLATION_TYPES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
    ]
    customer = models.ForeignKey('customer_data.CustomerProfile', on_delete=models.CASCADE, related_name='installation_requests', verbose_name=_("Customer Profile"))
    associated_order = models.ForeignKey(
        Order, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='installation_requests',
        verbose_name=_("Associated Order") # More explicit name
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    installation_type = models.CharField(max_length=20, choices=INSTALLATION_TYPES)
    
    order_number = models.CharField(_("Order Number"), max_length=100, blank=True, null=True, db_index=True)
    assessment_number = models.CharField(_("Assessment Number"), max_length=100, blank=True, null=True, db_index=True)
    full_name = models.CharField(_("Contact Full Name"), max_length=255, help_text=_("Full name of the contact requesting the installation"))
    address = models.TextField(_("Installation Address"))
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    preferred_datetime = models.CharField(_("Preferred Date/Time"), max_length=255)
    contact_phone = models.CharField(_("Contact Phone"), max_length=20)
    branch = models.CharField(_("Branch"), max_length=100, blank=True, null=True)
    sales_person_name = models.CharField(_("Sales Person Name"), max_length=255, blank=True, null=True)
    availability = models.CharField(_("Availability"), max_length=50, blank=True, null=True)
    alternative_contact_name = models.CharField(_("Alternative Contact Name"), max_length=255, blank=True, null=True)
    alternative_contact_number = models.CharField(_("Alternative Contact Number"), max_length=20, blank=True, null=True)
    notes = models.TextField(_("Installation Notes"), blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Installation for {self.full_name} ({self.status})"

class SiteAssessmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('assessed', 'Assessed'),
        ('cancelled', 'Cancelled'),
    ]
    assessment_id = models.CharField(_("Assessment ID"), max_length=100, unique=True, blank=True, null=True, db_index=True)
    customer = models.ForeignKey('customer_data.CustomerProfile', on_delete=models.CASCADE, related_name='assessment_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    full_name = models.CharField(_("Full Name"), max_length=255)
    company_name = models.CharField(_("Company Name"), max_length=255, blank=True, null=True)
    address = models.TextField(_("Assessment Address"))
    contact_info = models.CharField(_("Contact Info"), max_length=255)
    preferred_day = models.CharField(_("Preferred Day"), max_length=255)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Assessment #{self.assessment_id or self.id} for {self.full_name} ({self.status})"
