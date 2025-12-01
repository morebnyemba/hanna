from django.contrib import admin
from .models import Retailer


@admin.register(Retailer)
class RetailerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'user', 'contact_phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['company_name', 'user__username', 'user__email', 'business_registration_number']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user']
