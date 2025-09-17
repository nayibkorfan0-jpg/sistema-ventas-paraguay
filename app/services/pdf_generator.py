import os
import io
from datetime import datetime
from decimal import Decimal
from typing import Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus.flowables import HRFlowable
from sqlalchemy.orm import Session

from app.models.sales import Quote
from app.models.invoice import Invoice
from app.models.company import CompanySettings
from app.core.database import get_database
from app.utils.paraguay_fiscal import ParaguayFiscalUtils, ParaguayFiscalValidator
from app.crud.company import company_settings_crud

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.darkblue,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=12
        )

    def generate_quote_pdf(self, quote: Quote, output_dir: str = "temp/pdfs") -> str:
        """Generar PDF de cotización"""
        
        # Crear directorio si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Nombre del archivo
        filename = f"cotizacion_{quote.quote_number}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        # Crear documento PDF
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )
        
        # Construir contenido
        story = []
        
        # Encabezado de empresa
        story.extend(self._create_company_header())
        story.append(Spacer(1, 20))
        
        # Título
        title = Paragraph("COTIZACIÓN", self.title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Información de cotización y cliente
        story.extend(self._create_quote_info(quote))
        story.append(Spacer(1, 20))
        
        # Tabla de productos/servicios
        story.extend(self._create_items_table(quote))
        story.append(Spacer(1, 20))
        
        # Totales
        story.extend(self._create_totals_table(quote))
        story.append(Spacer(1, 20))
        
        # Términos y condiciones
        if quote.terms_conditions:
            story.extend(self._create_terms_section(quote.terms_conditions))
        
        # Notas adicionales
        if quote.notes:
            story.extend(self._create_notes_section(quote.notes))
        
        # Pie de página
        story.extend(self._create_footer())
        
        # Construir PDF
        doc.build(story)
        
        return filepath

    def _create_company_header(self, db: Session = None):
        """Crear encabezado de empresa con datos paraguayos"""
        # Obtener configuración de empresa desde la base de datos
        company_settings = None
        if db:
            try:
                company_settings = company_settings_crud.get_settings(db)
            except:
                pass
        
        if company_settings:
            # Header con datos reales de la empresa paraguaya - obtener valores actuales
            razon_social_val = getattr(company_settings, 'razon_social', '') or ''
            ruc_val = getattr(company_settings, 'ruc', '') or ''
            direccion_val = getattr(company_settings, 'direccion', '') or ''
            telefono_val = getattr(company_settings, 'telefono', '') or ''
            email_val = getattr(company_settings, 'email', '') or ''
            timbrado_val = getattr(company_settings, 'timbrado', '') or ''
            punto_expedicion_val = getattr(company_settings, 'punto_expedicion', '') or ''
            
            company_data = [
                [razon_social_val, ""],
                [f"RUC: {ruc_val}", f"Tel: {telefono_val}"],
                [direccion_val, f"Email: {email_val}"],
                [f"Timbrado: {timbrado_val}", f"Punto Exp.: {punto_expedicion_val}"]
            ]
        else:
            # Fallback si no hay configuración
            company_data = [
                ["SISTEMA DE GESTIÓN DE VENTAS", ""],
                ["RUC: 80123456-7", "Tel: +595 21 123 456"],
                ["Asunción, Paraguay", "Email: ventas@empresa.com"],
                ["Timbrado: 12345678", "Punto Exp.: 001"]
            ]
        
        company_table = Table(company_data, colWidths=[3*inch, 3*inch])
        company_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 14),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        return [company_table, HRFlowable(width="100%", thickness=1, color=colors.darkblue)]

    def _create_quote_info(self, quote: Quote):
        """Crear información de cotización y cliente"""
        # Información de cotización
        quote_data = [
            ["Número de Cotización:", quote.quote_number],
            ["Fecha:", quote.quote_date.strftime("%d/%m/%Y")],
            ["Válida hasta:", quote.valid_until.strftime("%d/%m/%Y")],
            ["Estado:", quote.status.upper()]
        ]
        
        quote_table = Table(quote_data, colWidths=[1.5*inch, 2*inch])
        quote_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        # Información del cliente
        customer = quote.customer
        customer_data = [
            ["Cliente:", customer.company_name],
            ["Contacto:", customer.contact_name or ""],
            ["Email:", customer.email or ""],
            ["Teléfono:", customer.phone or ""]
        ]
        
        customer_table = Table(customer_data, colWidths=[1.5*inch, 2*inch])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        # Tabla combinada
        main_table = Table([[quote_table, customer_table]], colWidths=[3.5*inch, 3.5*inch])
        main_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        return [main_table]

    def _create_items_table(self, quote: Quote):
        """Crear tabla de productos/servicios"""
        # Encabezados
        headers = ["Descripción", "Cantidad", "Precio Unit.", "Descuento", "Total"]
        
        # Datos de los productos
        data = [headers]
        
        for line in quote.lines:
            product_name = line.product.name if line.product else "Producto"
            description = line.description or product_name
            
            row = [
                description,
                str(line.quantity),
                f"${line.unit_price:,.2f}",
                f"{line.discount_percent}%",
                f"${line.line_total:,.2f}"
            ]
            data.append(row)
        
        # Crear tabla
        items_table = Table(data, colWidths=[2.5*inch, 0.8*inch, 1*inch, 0.8*inch, 1*inch])
        items_table.setStyle(TableStyle([
            # Encabezados
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # Datos
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Alineación derecha para números
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),   # Alineación izquierda para descripción
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Alternar colores de filas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        return [Paragraph("Detalle de Productos/Servicios", self.header_style), items_table]

    def _create_totals_table(self, quote: Quote):
        """Crear tabla de totales"""
        totals_data = [
            ["Subtotal:", f"${quote.subtotal:,.2f}"],
            ["IVA (16%):", f"${quote.tax_amount:,.2f}"],
            ["TOTAL:", f"${quote.total_amount:,.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[1.5*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 1), 10),
            ('FONTSIZE', (0, 2), (-1, 2), 12),  # Total más grande
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 2), (-1, 2), colors.lightblue),  # Resaltar total
        ]))
        
        # Tabla para alinear a la derecha
        main_table = Table([[" ", totals_table]], colWidths=[4.5*inch, 3*inch])
        
        return [main_table]

    def _create_terms_section(self, terms: str):
        """Crear sección de términos y condiciones"""
        header = Paragraph("Términos y Condiciones", self.header_style)
        content = Paragraph(terms, self.styles['Normal'])
        
        return [header, content, Spacer(1, 12)]

    def _create_notes_section(self, notes: str):
        """Crear sección de notas"""
        header = Paragraph("Notas Adicionales", self.header_style)
        content = Paragraph(notes, self.styles['Normal'])
        
        return [header, content, Spacer(1, 12)]

    def _create_footer(self):
        """Crear pie de página"""
        footer_text = f"Cotización generada el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        footer = Paragraph(footer_text, self.styles['Normal'])
        
        return [Spacer(1, 20), HRFlowable(width="100%", thickness=0.5, color=colors.grey), footer]

    def generate_invoice_pdf(self, invoice: Invoice, db: Session = None) -> io.BytesIO:
        """Generar PDF de factura y devolver como BytesIO buffer"""
        
        # Crear buffer en memoria
        buffer = io.BytesIO()
        
        # Crear documento PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )
        
        # Construir contenido
        story = []
        
        # Encabezado de empresa paraguaya
        story.extend(self._create_company_header(db))
        story.append(Spacer(1, 20))
        
        # Título
        title = Paragraph("FACTURA", self.title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Información de factura y cliente
        story.extend(self._create_invoice_info(invoice))
        story.append(Spacer(1, 20))
        
        # Tabla de productos/servicios
        story.extend(self._create_invoice_items_table(invoice))
        story.append(Spacer(1, 20))
        
        # Totales con desglose paraguayo
        story.extend(self._create_paraguay_invoice_totals(invoice))
        story.append(Spacer(1, 20))
        
        # Términos de pago
        if invoice.payment_terms:
            story.extend(self._create_payment_terms_section(invoice.payment_terms))
        
        # Notas adicionales
        if invoice.notes:
            story.extend(self._create_notes_section(invoice.notes))
        
        # Pie de página
        story.extend(self._create_footer())
        
        # Construir PDF
        doc.build(story)
        
        return buffer

    def _create_invoice_info(self, invoice: Invoice):
        """Crear información de factura y cliente"""
        # Información de factura
        invoice_data = [
            ["Número de Factura:", invoice.invoice_number],
            ["Fecha de Factura:", invoice.invoice_date.strftime("%d/%m/%Y")],
            ["Fecha de Vencimiento:", invoice.due_date.strftime("%d/%m/%Y")],
            ["Estado:", invoice.status.upper()]
        ]
        
        invoice_table = Table(invoice_data, colWidths=[1.5*inch, 2*inch])
        invoice_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        # Información del cliente
        customer = invoice.customer
        customer_data = [
            ["Cliente:", customer.company_name if customer else "Cliente"],
            ["RFC/ID:", customer.tax_id if customer and hasattr(customer, 'tax_id') else ""],
            ["Email:", customer.email or ""],
            ["Teléfono:", customer.phone or ""]
        ]
        
        customer_table = Table(customer_data, colWidths=[1.5*inch, 2*inch])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        # Tabla combinada
        main_table = Table([[invoice_table, customer_table]], colWidths=[3.5*inch, 3.5*inch])
        main_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        return [main_table]

    def _create_invoice_items_table(self, invoice: Invoice):
        """Crear tabla de productos/servicios de factura"""
        # Encabezados
        headers = ["Descripción", "Cantidad", "Precio Unit.", "Descuento", "Total"]
        
        # Datos de los productos
        data = [headers]
        
        for line in invoice.lines:
            product_name = line.product.name if line.product else "Producto"
            description = line.description or product_name
            
            row = [
                description,
                str(line.quantity),
                f"${line.unit_price:,.2f}",
                f"{line.discount_percent}%",
                f"${line.line_total:,.2f}"
            ]
            data.append(row)
        
        # Crear tabla
        items_table = Table(data, colWidths=[2.5*inch, 0.8*inch, 1*inch, 0.8*inch, 1*inch])
        items_table.setStyle(TableStyle([
            # Encabezados
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # Datos
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Alineación derecha para números
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),   # Alineación izquierda para descripción
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Alternar colores de filas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        return [Paragraph("Detalle de Productos/Servicios", self.header_style), items_table]

    def _create_invoice_totals_table(self, invoice: Invoice):
        """Crear tabla de totales de factura"""
        totals_data = [
            ["Subtotal:", f"${invoice.subtotal:,.2f}"],
            ["IVA (16%):", f"${invoice.tax_amount:,.2f}"],
            ["TOTAL:", f"${invoice.total_amount:,.2f}"],
            ["Pagado:", f"${invoice.paid_amount:,.2f}"],
            ["Saldo Pendiente:", f"${invoice.balance_due:,.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[1.5*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 3), 10),
            ('FONTSIZE', (0, 2), (0, 2), 12),  # Total más grande
            ('FONTSIZE', (0, 4), (0, 4), 11),  # Saldo pendiente destacado
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 2), (-1, 2), colors.lightblue),  # Resaltar total
            ('BACKGROUND', (0, 4), (-1, 4), colors.lightyellow),  # Resaltar saldo
        ]))
        
        # Tabla para alinear a la derecha
        main_table = Table([[" ", totals_table]], colWidths=[4.5*inch, 3*inch])
        
        return [main_table]

    def _create_payment_terms_section(self, terms: str):
        """Crear sección de términos de pago"""
        header = Paragraph("Términos de Pago", self.header_style)
        content = Paragraph(terms, self.styles['Normal'])
        
        return [header, content, Spacer(1, 12)]
    
    def _create_paraguay_invoice_totals(self, invoice: Invoice):
        """Crear tabla de totales con desglose paraguayo"""
        currency = getattr(invoice, 'currency', 'PYG')
        
        # Datos para la tabla de totales paraguaya
        totals_data = [
            ["Subtotal Gravado 10%:", ParaguayFiscalUtils.format_currency(getattr(invoice, 'subtotal_gravado_10', 0), currency)],
            ["Subtotal Gravado 5%:", ParaguayFiscalUtils.format_currency(getattr(invoice, 'subtotal_gravado_5', 0), currency)],
            ["Subtotal Exento:", ParaguayFiscalUtils.format_currency(getattr(invoice, 'subtotal_exento', 0), currency)],
            ["IVA 10%:", ParaguayFiscalUtils.format_currency(getattr(invoice, 'iva_10', 0), currency)],
            ["IVA 5%:", ParaguayFiscalUtils.format_currency(getattr(invoice, 'iva_5', 0), currency)]
        ]
        
        # Agregar régimen turístico si aplica
        if getattr(invoice, 'tourism_regime_applied', False):
            tourism_percent = getattr(invoice, 'tourism_regime_percentage', 0)
            totals_data.append([f"Exención Turística ({tourism_percent}%):", 
                               ParaguayFiscalUtils.format_currency(getattr(invoice, 'iva_10', 0) + getattr(invoice, 'iva_5', 0) - invoice.tax_amount, currency)])
        
        totals_data.extend([
            ["TOTAL:", ParaguayFiscalUtils.format_currency(invoice.total_amount, currency)],
            ["Pagado:", ParaguayFiscalUtils.format_currency(invoice.paid_amount, currency)],
            ["Saldo Pendiente:", ParaguayFiscalUtils.format_currency(invoice.balance_due, currency)]
        ])
        
        # Información fiscal adicional
        fiscal_info = [
            ["Condición de Venta:", ParaguayFiscalUtils.get_condicion_venta_display(getattr(invoice, 'condicion_venta', 'CREDITO'))],
            ["Lugar de Emisión:", getattr(invoice, 'lugar_emision', 'Asunción')]
        ]
        
        totals_table = Table(totals_data, colWidths=[2*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -3), 9),
            ('FONTSIZE', (0, -3), (0, -3), 11),  # Total más grande
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -3), (-1, -3), colors.lightblue),  # Resaltar total
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightyellow),  # Resaltar saldo
        ]))
        
        fiscal_table = Table(fiscal_info, colWidths=[2*inch, 1.5*inch])
        fiscal_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        # Tabla principal para alinear a la derecha
        main_table = Table([[" ", totals_table]], colWidths=[3.5*inch, 3.5*inch])
        fiscal_main_table = Table([[" ", fiscal_table]], colWidths=[3.5*inch, 3.5*inch])
        
        return [main_table, Spacer(1, 10), fiscal_main_table]

# Instancia global
pdf_generator = PDFGenerator()