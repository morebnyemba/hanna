from django.contrib import admin
from .models import CustomerProfile, Interaction, Order, OrderItem, InstallationRequest, SiteAssessmentRequest, SolarCleaningRequest, JobCard, LoanApplication, Payment, ClientClaimToken
from warranty.admin import TechnicianCommentInline

class InteractionInline(admin.TabularInline):
    """
    Inline admin for displaying recent interactions directly on the CustomerProfile page.
    This provides immediate context about recent activities.
    """
    model = Interaction
    extra = 0  # Don't show extra empty forms for new interactions
    fields = ('created_at', 'interaction_type', 'agent', 'notes_preview')
    readonly_fields = ('created_at', 'interaction_type', 'agent', 'notes_preview')
    show_change_link = True  # Allow clicking to the full interaction change form
    ordering = ('-created_at',)
    verbose_name_plural = 'Recent Interactions'

    def notes_preview(self, obj):
        """Provides a truncated preview of the interaction notes."""
        if obj.notes:
            return (obj.notes[:75] + '...') if len(obj.notes) > 75 else obj.notes
        return "No notes."
    notes_preview.short_description = "Notes Preview"

    def has_add_permission(self, request, obj=None):
        # Interactions should be added via the API or main Interaction admin, not inline.
        return False

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for the CustomerProfile model.
    """
    list_display = ('__str__', 'lead_status', 'company', 'assigned_agent', 'last_interaction_date')
    list_filter = ('lead_status', 'assigned_agent', 'country', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'company', 'contact__whatsapp_id', 'contact__name')
    readonly_fields = ('contact', 'created_at', 'updated_at', 'last_interaction_date')
    inlines = [InteractionInline]
    list_per_page = 25
    list_select_related = ('contact', 'assigned_agent') # Performance optimization

    fieldsets = (
        ('Primary Info', {
            'fields': ('contact', ('first_name', 'last_name'), 'email')
        }),
        ('Company & Role', {
            'fields': ('company', 'role')
        }),
        ('Sales Pipeline', {
            'fields': ('lead_status', 'potential_value', 'acquisition_source', 'assigned_agent')
        }),
        ('Location', {
            'fields': (('city', 'state_province'), ('postal_code', 'country')),
            'classes': ('collapse',) # Collapsible section
        }),
        ('Segmentation & Notes', {
            'fields': ('tags', 'notes', 'custom_attributes')
        }),
        ('System Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_interaction_date'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    """
    Admin interface for the Interaction model.
    """
    list_display = ('__str__', 'customer', 'agent', 'interaction_type', 'created_at')
    list_filter = ('interaction_type', 'agent', 'created_at')
    search_fields = ('notes', 'customer__first_name', 'customer__last_name', 'customer__contact__whatsapp_id')
    readonly_fields = ('created_at',)
    list_per_page = 30
    list_select_related = ('customer', 'agent', 'customer__contact') # Performance optimization
    autocomplete_fields = ['customer', 'agent'] # Use a search-friendly widget for foreign keys

    fieldsets = (
        (None, {
            'fields': ('customer', 'agent', 'interaction_type')
        }),
        ('Details', {
            'fields': ('notes', 'created_at')
        }),
    )

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fk_name = "order"
    extra = 1  # Show 1 empty slot for a new OrderItem
    autocomplete_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'name', 'customer', 'stage', 'payment_status', 'amount', 'currency', 'assigned_agent', 'created_at')
    list_filter = ('stage', 'payment_status', 'assigned_agent', 'currency', 'created_at')
    search_fields = ('order_number', 'name', 'customer__first_name', 'customer__last_name', 'customer__company')
    autocomplete_fields = ['customer', 'assigned_agent']
    list_editable = ('stage', 'payment_status',)
    readonly_fields = ()
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    fieldsets = (
        (None, {'fields': ('order_number', 'name', 'customer', 'assigned_agent')}),
        ('Deal Details', {'fields': ('stage', 'payment_status', ('amount', 'currency'), 'expected_close_date')}),
        ('Notes', {'fields': ('notes',)}),
    )
    list_select_related = ('customer', 'assigned_agent')

@admin.register(InstallationRequest)
class InstallationRequestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'installation_type', 'status', 'associated_order', 'preferred_datetime', 'created_at')
    list_filter = ('status', 'installation_type', 'created_at')
    search_fields = ('full_name', 'order_number', 'assessment_number', 'address', 'contact_phone', 'associated_order__name', 'associated_order__order_number')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['customer', 'associated_order']

@admin.register(SiteAssessmentRequest)
class SiteAssessmentRequestAdmin(admin.ModelAdmin):
    list_display = ('assessment_id', 'full_name', 'company_name', 'status', 'preferred_day', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('assessment_id', 'full_name', 'company_name', 'address', 'contact_info')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['customer']
    list_editable = ('status',)

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'loan_type', 'status', 'requested_amount', 'product_of_interest', 'created_at')
    search_fields = ('full_name', 'national_id', 'customer__contact__name', 'customer__contact__whatsapp_id')
    list_filter = ('status', 'loan_type', 'employment_status', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['customer']

@admin.register(SolarCleaningRequest)
class SolarCleaningRequestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'status', 'preferred_date', 'roof_type', 'panel_count', 'created_at')
    list_filter = ('status', 'roof_type', 'panel_type', 'availability', 'created_at')
    search_fields = ('full_name', 'contact_phone', 'address')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['customer']
    list_editable = ('status',)
    fieldsets = (
        ('Request Details', {
            'fields': ('customer', 'status', 'full_name', 'contact_phone')
        }),
        ('Job Specifications', {
            'fields': ('roof_type', 'panel_type', 'panel_count')
        }),
        ('Scheduling & Location', {
            'fields': ('preferred_date', 'availability', 'address', ('latitude', 'longitude'))
        }),
    )
    list_editable = ('status',)

@admin.register(JobCard)
class JobCardAdmin(admin.ModelAdmin):
    list_display = ('job_card_number', 'customer', 'serialized_item', 'status', 'is_under_warranty', 'warranty_claim', 'creation_date')
    list_filter = ('status', 'is_under_warranty', 'creation_date')
    search_fields = ('job_card_number', 'customer__first_name', 'customer__last_name', 'serialized_item__serial_number', 'serialized_item__product__name', 'reported_fault')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['customer', 'warranty_claim', 'serialized_item']
    list_editable = ('status',)
    inlines = [TechnicianCommentInline,]
    date_hierarchy = 'creation_date'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin interface for the Payment model.
    """
    list_display = ('short_id', 'customer', 'order', 'amount', 'currency', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'currency', 'created_at')
    search_fields = ('id', 'customer__first_name', 'customer__last_name', 'provider_transaction_id', 'order__order_number')
    autocomplete_fields = ('customer', 'order')
    readonly_fields = ('id', 'created_at', 'updated_at', 'provider_response')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('id', 'customer', 'order')
        }),
        ('Amount & Method', {
            'fields': ('amount', 'currency', 'payment_method', 'status')
        }),
        ('Provider Details', {
            'fields': ('provider_transaction_id', 'poll_url', 'provider_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def short_id(self, obj):
        """Display shortened UUID for readability"""
        return f"{str(obj.id)[:8]}"
    short_id.short_description = "Payment ID"
    short_id.admin_order_field = 'id'

@admin.register(ClientClaimToken)
class ClientClaimTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for managing client claim tokens.
    Allows admins to generate claim links and track their status.
    """
    list_display = ('token_preview', 'isr_display', 'customer_display', 'status_badge', 'created_at', 'expires_at', 'claim_link')
    list_filter = ('claimed', 'created_at', 'expires_at')
    search_fields = ('token', 'installation_system_record__installation_address', 'installation_system_record__customer__first_name')
    readonly_fields = ('token', 'created_at', 'expires_at', 'claimed_at', 'claim_link', 'claim_link_info')
    
    fieldsets = (
        ('Token Information', {
            'fields': ('token', 'claim_link', 'claim_link_info')
        }),
        ('Installation Details', {
            'fields': ('installation_system_record',)
        }),
        ('Creation', {
            'fields': ('created_by', 'created_at')
        }),
        ('Expiration', {
            'fields': ('expires_at',)
        }),
        ('Claim Status', {
            'fields': ('claimed', 'claimed_at', 'claimed_by_user'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_claimed']

    def token_preview(self, obj):
        """Show truncated token in list"""
        return f"{obj.token[:16]}..."
    token_preview.short_description = "Token"

    def isr_display(self, obj):
        """Show ISR address"""
        return obj.installation_system_record.installation_address
    isr_display.short_description = "Installation"

    def customer_display(self, obj):
        """Show customer name"""
        customer = obj.installation_system_record.customer
        if customer:
            return customer.get_full_name()
        return "—"
    customer_display.short_description = "Customer"

    def status_badge(self, obj):
        """Show claim status"""
        if obj.claimed:
            return '✓ Claimed'
        elif obj.is_expired():
            return '✗ Expired'
        else:
            return '○ Active'
    status_badge.short_description = "Status"

    def claim_link(self, obj):
        """Generate the shareable claim link"""
        from django.conf import settings
        domain = settings.DOMAIN if hasattr(settings, 'DOMAIN') else 'hanna.co.zw'
        link = f"https://{domain}/client/claim/{obj.token}"
        return f'<a href="{link}" target="_blank">{link}</a>'
    claim_link.allow_tags = True
    claim_link.short_description = "Claim Link"

    def claim_link_info(self, obj):
        """Display copy-friendly claim link and instructions"""
        from django.conf import settings
        domain = settings.DOMAIN if hasattr(settings, 'DOMAIN') else 'hanna.co.zw'
        link = f"https://{domain}/client/claim/{obj.token}"
        
        status = "✓ Already claimed" if obj.claimed else f"⏱ Expires {obj.expires_at.strftime('%Y-%m-%d %H:%M')}"
        
        return f"""
        <strong>Share this link with the customer:</strong>
        <br/>
        <code style="background: #f0f0f0; padding: 10px; display: block; margin: 10px 0; word-break: break-all;">{link}</code>
        <strong>Status:</strong> {status}
        <br/>
        <small>Token: {obj.token}</small>
        """
    claim_link_info.allow_tags = True
    claim_link_info.short_description = "Share This Link"

    def mark_claimed(self, request, queryset):
        """Admin action to manually mark tokens as claimed"""
        updated = queryset.filter(claimed=False).update(claimed=True)
        self.message_user(request, f'{updated} tokens marked as claimed.')
    mark_claimed.short_description = "Mark selected as claimed"

    def has_add_permission(self, request):
        # Tokens are generated via ISR admin actions, not manually created
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent accidental deletion of claim tokens
        return request.user.is_superuser