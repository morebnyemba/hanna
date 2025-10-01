from django.contrib import admin
from .models import EmailAttachment, ParsedInvoice

class ParsedInvoiceInline(admin.StackedInline):
    model = ParsedInvoice
    extra = 0
    readonly_fields = ('invoice_number', 'invoice_date', 'total_amount', 'extracted_at', 'updated_at')

@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'sender', 'subject', 'processed', 'saved_at', 'email_date')
    list_filter = ('processed', 'sender', 'email_date')
    search_fields = ('filename', 'subject', 'sender', 'ocr_text')
    readonly_fields = ('saved_at', 'updated_at', 'ocr_text')
    fieldsets = (
        (None, {'fields': ('filename', 'sender', 'subject', 'email_date', 'processed')}),
        ('File Info', {'fields': ('file',)}),
        ('Timestamps', {'fields': ('saved_at', 'updated_at')}),
        ('OCR Result', {'classes': ('collapse',), 'fields': ('ocr_text',)}),
    )
    inlines = [ParsedInvoiceInline]