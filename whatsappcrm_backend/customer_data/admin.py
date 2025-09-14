from django.contrib import admin
from .models import CustomerProfile, Interaction, Order, OrderItem, InstallationRequest, SiteAssessmentRequest

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
    list_display = ('order_number', 'name', 'customer', 'stage', 'amount', 'currency', 'assigned_agent', 'created_at')
    list_filter = ('stage', 'assigned_agent', 'currency', 'created_at')
    search_fields = ('order_number', 'name', 'customer__first_name', 'customer__last_name', 'customer__company')
    autocomplete_fields = ['customer', 'assigned_agent']
    list_editable = ('stage',)
    readonly_fields = ('amount',)
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    fieldsets = (
        (None, {'fields': ('order_number', 'name', 'customer', 'assigned_agent')}),
        ('Deal Details', {'fields': ('stage', ('amount', 'currency'), 'expected_close_date')}),
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
    list_display = ('full_name', 'company_name', 'status', 'preferred_day', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('full_name', 'company_name', 'address', 'contact_info')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['customer']