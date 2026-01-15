"""
PDF Generation utilities for Warranty Certificates and Installation Reports.
Uses ReportLab for PDF generation and QR codes for digital record linking.
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from io import BytesIO
import qrcode
from django.conf import settings
from datetime import datetime
import os


class PDFGenerator:
    """Base class for PDF generation with common utilities"""
    
    def __init__(self):
        self.page_width, self.page_height = A4
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),  # Dark blue
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3b82f6'),  # Blue
            spaceAfter=12,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Company name style
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#059669'),  # Green (Pfungwa color)
            spaceAfter=5,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Info style
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=6,
            alignment=TA_LEFT
        ))
        
        # Small text style
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            spaceAfter=3,
            alignment=TA_LEFT
        ))
    
    def generate_qr_code(self, data, size=100):
        """
        Generate QR code image for embedding in PDF
        
        Args:
            data: String data to encode in QR code
            size: Size of QR code in pixels
            
        Returns:
            Image object for reportlab
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO buffer
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Create reportlab Image
        qr_image = Image(buffer, width=size, height=size)
        return qr_image
    
    def add_header(self, elements):
        """Add company header to PDF"""
        # Company name
        elements.append(Paragraph("PFUNGWA", self.styles['CompanyName']))
        elements.append(Paragraph("Solar & Technology Solutions", self.styles['InfoText']))
        elements.append(Spacer(1, 0.2*inch))
    
    def add_footer_info(self, elements):
        """Add footer information to PDF"""
        footer_data = [
            ['Contact:', 'Email: info@pfungwa.co.zw'],
            ['', 'Phone: +263 XX XXX XXXX'],
            ['', 'Website: www.pfungwa.co.zw']
        ]
        
        footer_table = Table(footer_data, colWidths=[1.5*inch, 4.5*inch])
        footer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(Spacer(1, 0.3*inch))
        elements.append(footer_table)
    
    def create_info_table(self, data, col_widths=None):
        """
        Create a styled table for information display
        
        Args:
            data: List of lists containing table data
            col_widths: Optional list of column widths
            
        Returns:
            Table object
        """
        if col_widths is None:
            col_widths = [2.5*inch, 4*inch]
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        return table


class WarrantyCertificateGenerator(PDFGenerator):
    """Generate warranty certificate PDFs"""
    
    def generate(self, warranty):
        """
        Generate warranty certificate PDF
        
        Args:
            warranty: Warranty model instance
            
        Returns:
            BytesIO buffer containing PDF data
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)
        
        elements = []
        
        # Header
        self.add_header(elements)
        
        # Certificate title
        elements.append(Paragraph("WARRANTY CERTIFICATE", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Certificate number and dates
        cert_info = [
            ['Certificate No:', f"WC-{warranty.id}"],
            ['Issue Date:', warranty.start_date.strftime('%d %B %Y')],
            ['Valid Until:', warranty.end_date.strftime('%d %B %Y')],
        ]
        elements.append(self.create_info_table(cert_info))
        elements.append(Spacer(1, 0.3*inch))
        
        # Customer details
        elements.append(Paragraph("Customer Details", self.styles['CustomSubtitle']))
        customer = warranty.customer
        customer_data = [
            ['Name:', customer.get_full_name() or 'N/A'],
            ['Contact:', customer.contact.whatsapp_id if customer.contact else 'N/A'],
            ['Email:', customer.email or 'N/A'],
        ]
        
        if customer.address_line_1:
            address_parts = [customer.address_line_1]
            if customer.address_line_2:
                address_parts.append(customer.address_line_2)
            if customer.city:
                address_parts.append(customer.city)
            address = ', '.join(address_parts)
            customer_data.append(['Address:', address])
        
        elements.append(self.create_info_table(customer_data))
        elements.append(Spacer(1, 0.3*inch))
        
        # Product/System details
        elements.append(Paragraph("System Specifications", self.styles['CustomSubtitle']))
        serialized_item = warranty.serialized_item
        product = serialized_item.product
        
        product_data = [
            ['Product Name:', product.name],
            ['SKU:', product.sku or 'N/A'],
            ['Serial Number:', serialized_item.serial_number],
        ]
        
        if serialized_item.barcode:
            product_data.append(['Barcode:', serialized_item.barcode])
        
        if warranty.manufacturer:
            product_data.append(['Manufacturer:', warranty.manufacturer.name])
        
        elements.append(self.create_info_table(product_data))
        elements.append(Spacer(1, 0.3*inch))
        
        # Warranty terms
        elements.append(Paragraph("Warranty Terms & Conditions", self.styles['CustomSubtitle']))
        
        terms = [
            "1. This warranty covers manufacturing defects and workmanship issues.",
            "2. Warranty is valid from the installation/purchase date shown above.",
            "3. Regular maintenance is required to keep warranty valid.",
            "4. Warranty does not cover damage from misuse, accidents, or natural disasters.",
            "5. All warranty claims must be reported within 7 days of discovery.",
            "6. Pfungwa reserves the right to repair or replace defective items at our discretion.",
            "7. This warranty is non-transferable.",
        ]
        
        for term in terms:
            elements.append(Paragraph(term, self.styles['SmallText']))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # QR Code section
        # Generate URL for digital verification
        qr_url = f"{getattr(settings, 'FRONTEND_URL', 'https://dashboard.hanna.co.zw')}/warranty/{warranty.id}"
        qr_image = self.generate_qr_code(qr_url, size=80)
        
        qr_data = [
            [qr_image, Paragraph("Scan for digital verification", self.styles['SmallText'])]
        ]
        qr_table = Table(qr_data, colWidths=[1*inch, 4.5*inch])
        qr_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ]))
        elements.append(qr_table)
        
        # Footer
        self.add_footer_info(elements)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer


class InstallationReportGenerator(PDFGenerator):
    """Generate installation report PDFs"""
    
    def generate(self, installation_record):
        """
        Generate installation report PDF
        
        Args:
            installation_record: InstallationSystemRecord model instance
            
        Returns:
            BytesIO buffer containing PDF data
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)
        
        elements = []
        
        # Header
        self.add_header(elements)
        
        # Report title
        elements.append(Paragraph("INSTALLATION REPORT", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Report info
        report_info = [
            ['Report ID:', installation_record.short_id],
            ['Installation Date:', installation_record.installation_date.strftime('%d %B %Y') if installation_record.installation_date else 'N/A'],
            ['Report Generated:', datetime.now().strftime('%d %B %Y %H:%M')],
        ]
        elements.append(self.create_info_table(report_info))
        elements.append(Spacer(1, 0.3*inch))
        
        # Customer details
        elements.append(Paragraph("Customer Details", self.styles['CustomSubtitle']))
        customer = installation_record.customer
        customer_data = [
            ['Name:', customer.get_full_name() or 'N/A'],
            ['Contact:', customer.contact.whatsapp_id if customer.contact else 'N/A'],
            ['Email:', customer.email or 'N/A'],
        ]
        
        if installation_record.installation_address:
            customer_data.append(['Installation Address:', installation_record.installation_address])
        
        elements.append(self.create_info_table(customer_data))
        elements.append(Spacer(1, 0.3*inch))
        
        # Installation details
        elements.append(Paragraph("Installation Details", self.styles['CustomSubtitle']))
        
        installation_data = [
            ['Installation Type:', installation_record.get_installation_type_display()],
            ['System Classification:', installation_record.get_system_classification_display()],
        ]
        
        if installation_record.system_size:
            installation_data.append([
                'System Size/Capacity:', 
                f"{installation_record.system_size} {installation_record.capacity_unit}"
            ])
        
        installation_data.append(['Status:', installation_record.get_installation_status_display()])
        
        if installation_record.commissioning_date:
            installation_data.append([
                'Commissioning Date:', 
                installation_record.commissioning_date.strftime('%d %B %Y')
            ])
        
        elements.append(self.create_info_table(installation_data))
        elements.append(Spacer(1, 0.3*inch))
        
        # Technicians
        technicians = installation_record.technicians.all()
        if technicians:
            elements.append(Paragraph("Installation Team", self.styles['CustomSubtitle']))
            tech_names = [str(tech) for tech in technicians]
            elements.append(Paragraph(', '.join(tech_names), self.styles['InfoText']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Installed components
        components = installation_record.installed_components.all()
        if components:
            elements.append(Paragraph("Installed Components", self.styles['CustomSubtitle']))
            
            component_data = [['Item', 'Serial Number', 'Status']]
            for component in components:
                component_data.append([
                    component.product.name,
                    component.serial_number,
                    component.get_status_display()
                ])
            
            component_table = Table(component_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
            component_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(component_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # Commissioning checklists
        checklist_entries = installation_record.checklist_entries.all()
        if checklist_entries:
            elements.append(Paragraph("Commissioning Checklists", self.styles['CustomSubtitle']))
            
            for entry in checklist_entries:
                checklist_data = [
                    ['Checklist:', entry.template.name],
                    ['Type:', entry.template.get_checklist_type_display()],
                    ['Completion:', f"{entry.completion_percentage}%"],
                    ['Status:', entry.get_completion_status_display()],
                ]
                
                if entry.completed_at:
                    checklist_data.append([
                        'Completed:', 
                        entry.completed_at.strftime('%d %B %Y %H:%M')
                    ])
                
                elements.append(self.create_info_table(checklist_data, col_widths=[2*inch, 4.5*inch]))
                
                # Show completed items summary
                if entry.completed_items:
                    completed_count = sum(
                        1 for item_id, item_data in entry.completed_items.items() 
                        if item_data.get('completed', False)
                    )
                    total_items = len(entry.template.items)
                    elements.append(Paragraph(
                        f"Items Completed: {completed_count} of {total_items}",
                        self.styles['SmallText']
                    ))
                
                elements.append(Spacer(1, 0.2*inch))
        
        # Installation photos
        photos = installation_record.photos.all()
        if photos:
            elements.append(PageBreak())
            elements.append(Paragraph("Installation Photos", self.styles['CustomSubtitle']))
            elements.append(Spacer(1, 0.2*inch))
            
            # Group photos by type
            photo_types = {}
            for photo in photos:
                photo_type = photo.get_photo_type_display()
                if photo_type not in photo_types:
                    photo_types[photo_type] = []
                photo_types[photo_type].append(photo)
            
            # Add photos organized by type
            for photo_type, type_photos in photo_types.items():
                elements.append(Paragraph(f"{photo_type}:", self.styles['InfoText']))
                
                for photo in type_photos[:4]:  # Limit to 4 photos per type for space
                    try:
                        # Get media asset file path
                        if hasattr(photo.media_asset, 'file') and photo.media_asset.file:
                            file_path = photo.media_asset.file.path
                            if os.path.exists(file_path):
                                img = Image(file_path, width=2*inch, height=2*inch)
                                img.hAlign = 'LEFT'
                                elements.append(img)
                                
                                if photo.caption:
                                    elements.append(Paragraph(photo.caption, self.styles['SmallText']))
                                
                                elements.append(Spacer(1, 0.1*inch))
                    except Exception as e:
                        # If image loading fails, just add a note
                        elements.append(Paragraph(
                            f"[Photo: {photo.caption or 'Image unavailable'}]",
                            self.styles['SmallText']
                        ))
                
                elements.append(Spacer(1, 0.2*inch))
        
        # Test results section
        elements.append(PageBreak())
        elements.append(Paragraph("Test Results & Sign-Off", self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        if installation_record.installation_status == 'commissioned' or installation_record.installation_status == 'active':
            elements.append(Paragraph(
                "✓ System has been successfully commissioned and tested.",
                self.styles['InfoText']
            ))
        else:
            elements.append(Paragraph(
                "System commissioning is pending completion.",
                self.styles['InfoText']
            ))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Signature section
        signature_data = [
            ['', ''],
            ['Technician Signature: ___________________', 'Customer Signature: ___________________'],
            ['', ''],
            ['Date: ___________________', 'Date: ___________________'],
        ]
        
        signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(signature_table)
        
        # QR Code section
        elements.append(Spacer(1, 0.4*inch))
        qr_url = f"{getattr(settings, 'FRONTEND_URL', 'https://dashboard.hanna.co.zw')}/installation/{installation_record.id}"
        qr_image = self.generate_qr_code(qr_url, size=80)
        
        qr_data = [
            [qr_image, Paragraph("Scan for digital record", self.styles['SmallText'])]
        ]
        qr_table = Table(qr_data, colWidths=[1*inch, 4.5*inch])
        qr_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ]))
        elements.append(qr_table)
        
        # Footer
        self.add_footer_info(elements)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
