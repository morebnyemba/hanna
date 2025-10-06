from django.contrib import admin
from .models import AIProvider

@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ('provider', 'is_active', 'updated_at')
    list_filter = ('provider', 'is_active')
    search_fields = ('provider',)
    fields = ('provider', 'api_key', 'is_active')
    ordering = ('provider',)