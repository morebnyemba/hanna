from django.contrib import admin
from .models import Retailer, RetailerBranch


class RetailerBranchInline(admin.TabularInline):
    model = RetailerBranch
    extra = 0
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Retailer)
class RetailerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'user', 'contact_phone', 'branch_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['company_name', 'user__username', 'user__email', 'business_registration_number']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user']
    inlines = [RetailerBranchInline]

    def branch_count(self, obj):
        return obj.branches.count()
    branch_count.short_description = 'Branches'


@admin.register(RetailerBranch)
class RetailerBranchAdmin(admin.ModelAdmin):
    list_display = ['branch_name', 'retailer', 'branch_code', 'contact_phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'retailer', 'created_at']
    search_fields = ['branch_name', 'branch_code', 'user__username', 'retailer__company_name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user', 'retailer']
