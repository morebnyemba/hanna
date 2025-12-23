# whatsappcrm_backend/customer_data/receipts.py

from io import BytesIO
from decimal import Decimal
from typing import Tuple, Optional
from django.conf import settings
from django.utils import timezone
import os
import uuid

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

from .models import Order, Payment


def generate_order_receipt_pdf(order: Order, payment: Optional[Payment] = None) -> Tuple[str, str]:
    """
    Generate a provisional receipt PDF for an order and optional payment.

    Returns a tuple of (absolute_file_path, relative_media_url)
    where relative_media_url is under settings.MEDIA_URL (e.g., /media/receipts/xxx.pdf)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('ReceiptTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#1a4d2e'), alignment=TA_CENTER, spaceAfter=6)
    story.append(Paragraph("Provisional Receipt", title_style))
    story.append(Paragraph(f"Order #{order.order_number}", styles['Heading3']))
    story.append(Spacer(1, 0.2*inch))

    # Customer/delivery info from order notes; customer name if available
    customer_name = None
    if order.customer and order.customer.get_full_name():
        customer_name = order.customer.get_full_name()
    elif order.customer and order.customer.contact and order.customer.contact.name:
        customer_name = order.customer.contact.name

    info_rows = [
        ["Date:", timezone.now().strftime("%Y-%m-%d %H:%M")],
        ["Customer:", customer_name or "N/A"],
        ["Payment Status:", order.get_payment_status_display()],
    ]
    if payment:
        info_rows.append(["Paynow Reference:", payment.provider_transaction_id or "-"])
    customer_table = Table(info_rows, colWidths=[1.7*inch, 4.8*inch])
    customer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(customer_table)
    story.append(Spacer(1, 0.25*inch))

    # Line items
    data = [["Item", "Qty", "Unit Price", "Line Total"]]
    total = Decimal('0.00')
    currency = order.currency or 'USD'
    for item in order.items.select_related('product').all():
        line_total = (item.total_amount or (item.unit_price or Decimal('0.00')) * item.quantity)
        total += line_total
        data.append([
            item.product.name,
            str(item.quantity),
            f"{currency} {(item.unit_price or Decimal('0.00')):.2f}",
            f"{currency} {line_total:.2f}",
        ])
    data.append(["", "", "Subtotal:", f"{currency} {total:.2f}"])

    items_table = Table(data, colWidths=[3.0*inch, 0.7*inch, 1.3*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a4d2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d4edda')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.25*inch))

    story.append(Paragraph("This is a provisional receipt for your records.", styles['Normal']))

    doc.build(story)
    pdf_content = buffer.getvalue()
    buffer.close()

    # Save to media/receipts
    filename = f"receipt_{order.order_number}_{uuid.uuid4().hex[:8]}.pdf"
    abs_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
    os.makedirs(abs_dir, exist_ok=True)
    abs_path = os.path.join(abs_dir, filename)
    with open(abs_path, 'wb') as f:
        f.write(pdf_content)

    rel_url = f"{settings.MEDIA_URL}receipts/{filename}"
    return abs_path, rel_url
