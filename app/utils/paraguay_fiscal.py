"""
Utilidades fiscales específicas para Paraguay
Incluye validación de RUC, cálculos de IVA, y validaciones de timbrado
"""

import re
from datetime import date, datetime
from typing import Optional, Dict, Tuple, Any
from decimal import Decimal

class ParaguayFiscalValidator:
    """Validador fiscal para Paraguay"""
    
    @staticmethod
    def validate_ruc(ruc: str) -> Dict[str, Any]:
        """
        Validar RUC paraguayo con dígito verificador
        
        Args:
            ruc: RUC a validar (puede incluir guiones)
            
        Returns:
            Dict con resultado de validación y información extraída
        """
        if not ruc:
            return {
                "valid": False,
                "error": "RUC no puede estar vacío",
                "ruc_clean": None,
                "dv": None
            }
        
        # Limpiar RUC (remover espacios y guiones)
        ruc_clean = re.sub(r'[^0-9]', '', ruc)
        
        if len(ruc_clean) < 6:
            return {
                "valid": False,
                "error": "RUC debe tener al menos 6 dígitos",
                "ruc_clean": ruc_clean,
                "dv": None
            }
        
        if len(ruc_clean) > 10:
            return {
                "valid": False,
                "error": "RUC no puede tener más de 10 dígitos",
                "ruc_clean": ruc_clean,
                "dv": None
            }
        
        # Extraer dígito verificador si existe
        if len(ruc_clean) >= 7:
            ruc_base = ruc_clean[:-1]
            dv_provided = ruc_clean[-1]
            
            # Calcular dígito verificador
            dv_calculated = ParaguayFiscalValidator._calculate_ruc_dv(ruc_base)
            
            if dv_provided != str(dv_calculated):
                return {
                    "valid": False,
                    "error": f"Dígito verificador incorrecto. Esperado: {dv_calculated}, Recibido: {dv_provided}",
                    "ruc_clean": ruc_clean,
                    "dv": dv_provided
                }
            
            return {
                "valid": True,
                "error": None,
                "ruc_clean": ruc_clean,
                "ruc_base": ruc_base,
                "dv": dv_provided,
                "formatted": f"{ruc_base}-{dv_provided}"
            }
        else:
            # RUC sin dígito verificador
            dv_calculated = ParaguayFiscalValidator._calculate_ruc_dv(ruc_clean)
            
            return {
                "valid": True,
                "error": None,
                "ruc_clean": ruc_clean,
                "ruc_base": ruc_clean,
                "dv": str(dv_calculated),
                "formatted": f"{ruc_clean}-{dv_calculated}"
            }
    
    @staticmethod
    def _calculate_ruc_dv(ruc_base: str) -> int:
        """
        Calcular dígito verificador para RUC paraguayo
        
        Args:
            ruc_base: Base del RUC sin dígito verificador
            
        Returns:
            Dígito verificador calculado
        """
        if not ruc_base or not ruc_base.isdigit():
            return 0
        
        # Algoritmo módulo 11 para RUC paraguayo
        multipliers = [2, 3, 4, 5, 6, 7, 2, 3, 4]
        total = 0
        
        # Procesar desde el último dígito hacia el primero
        ruc_reversed = ruc_base[::-1]
        
        for i, digit in enumerate(ruc_reversed):
            if i < len(multipliers):
                total += int(digit) * multipliers[i]
        
        remainder = total % 11
        
        if remainder < 2:
            return remainder
        else:
            return 11 - remainder
    
    @staticmethod
    def validate_timbrado(timbrado: str, fecha_vencimiento: Optional[date] = None) -> Dict[str, any]:
        """
        Validar timbrado paraguayo
        
        Args:
            timbrado: Número de timbrado
            fecha_vencimiento: Fecha de vencimiento del timbrado
            
        Returns:
            Dict con resultado de validación
        """
        if not timbrado:
            return {
                "valid": False,
                "error": "Timbrado no puede estar vacío"
            }
        
        # Limpiar timbrado
        timbrado_clean = re.sub(r'[^0-9]', '', timbrado)
        
        if not timbrado_clean.isdigit():
            return {
                "valid": False,
                "error": "Timbrado debe contener solo números"
            }
        
        if len(timbrado_clean) < 8:
            return {
                "valid": False,
                "error": "Timbrado debe tener al menos 8 dígitos"
            }
        
        # Validar fecha de vencimiento
        if fecha_vencimiento:
            today = date.today()
            if fecha_vencimiento < today:
                return {
                    "valid": False,
                    "error": f"Timbrado vencido. Fecha de vencimiento: {fecha_vencimiento}",
                    "expired": True,
                    "days_expired": (today - fecha_vencimiento).days
                }
            
            # Advertir si está próximo a vencer (30 días)
            days_to_expire = (fecha_vencimiento - today).days
            if days_to_expire <= 30:
                return {
                    "valid": True,
                    "error": None,
                    "warning": f"Timbrado vence en {days_to_expire} días",
                    "days_to_expire": days_to_expire
                }
        
        return {
            "valid": True,
            "error": None,
            "timbrado_clean": timbrado_clean
        }
    
    @staticmethod
    def format_invoice_number(numero_actual: int, punto_expedicion: str = "001", timbrado: str = "") -> str:
        """
        Formatear número de factura paraguayo
        
        Args:
            numero_actual: Número actual de factura
            punto_expedicion: Punto de expedición (ej: "001")
            timbrado: Número de timbrado
            
        Returns:
            Número de factura formateado
        """
        # Asegurar que punto de expedición tenga 3 dígitos
        punto_expedicion = punto_expedicion.zfill(3)
        
        # Formatear número con 7 dígitos
        numero_formateado = str(numero_actual).zfill(7)
        
        return f"{punto_expedicion}-{numero_formateado}"

class ParaguayIVACalculator:
    """Calculadora de IVA para Paraguay"""
    
    @staticmethod
    def calculate_iva_breakdown(lines: list, iva_10_rate: Decimal = Decimal("10"), 
                              iva_5_rate: Decimal = Decimal("5")) -> Dict[str, Decimal]:
        """
        Calcular desglose de IVA paraguayo
        
        Args:
            lines: Lista de líneas con iva_category y line_total
            iva_10_rate: Tasa de IVA 10%
            iva_5_rate: Tasa de IVA 5%
            
        Returns:
            Dict con desglose de IVA
        """
        subtotal_gravado_10 = Decimal("0")
        subtotal_gravado_5 = Decimal("0")
        subtotal_exento = Decimal("0")
        
        for line in lines:
            line_total = Decimal(str(line.get("line_total", 0)))
            iva_category = line.get("iva_category", "10").upper()
            
            if iva_category == "10":
                subtotal_gravado_10 += line_total
            elif iva_category == "5":
                subtotal_gravado_5 += line_total
            else:  # EXENTO
                subtotal_exento += line_total
        
        # Calcular IVA
        iva_10 = subtotal_gravado_10 * (iva_10_rate / Decimal("100"))
        iva_5 = subtotal_gravado_5 * (iva_5_rate / Decimal("100"))
        
        total_iva = iva_10 + iva_5
        subtotal = subtotal_gravado_10 + subtotal_gravado_5 + subtotal_exento
        total = subtotal + total_iva
        
        return {
            "subtotal_gravado_10": subtotal_gravado_10,
            "subtotal_gravado_5": subtotal_gravado_5,
            "subtotal_exento": subtotal_exento,
            "iva_10": iva_10,
            "iva_5": iva_5,
            "total_iva": total_iva,
            "subtotal": subtotal,
            "total": total
        }
    
    @staticmethod
    def apply_tourism_regime(totals: Dict[str, Decimal], 
                           tourism_percentage: Decimal = Decimal("0")) -> Dict[str, Decimal]:
        """
        Aplicar régimen turístico paraguayo
        
        Args:
            totals: Totales calculados sin régimen turístico
            tourism_percentage: Porcentaje de exención turística
            
        Returns:
            Totales con régimen turístico aplicado
        """
        if tourism_percentage <= 0:
            return totals
        
        # Calcular descuento por régimen turístico
        tourism_discount_factor = tourism_percentage / Decimal("100")
        
        # El régimen turístico aplica sobre el IVA
        iva_10_discount = totals["iva_10"] * tourism_discount_factor
        iva_5_discount = totals["iva_5"] * tourism_discount_factor
        total_iva_discount = iva_10_discount + iva_5_discount
        
        # Actualizar totales
        new_totals = totals.copy()
        new_totals["iva_10"] -= iva_10_discount
        new_totals["iva_5"] -= iva_5_discount
        new_totals["total_iva"] -= total_iva_discount
        new_totals["total"] -= total_iva_discount
        new_totals["tourism_discount"] = total_iva_discount
        
        return new_totals

class ParaguayFiscalUtils:
    """Utilidades generales fiscales para Paraguay"""
    
    @staticmethod
    def format_invoice_number(numero_actual: int, punto_expedicion: str = "001", timbrado: str = "") -> str:
        """Formatear número de factura paraguayo - Delegado a ParaguayFiscalValidator"""
        return ParaguayFiscalValidator.format_invoice_number(numero_actual, punto_expedicion, timbrado)
    
    @staticmethod
    def get_condicion_venta_display(condicion: str) -> str:
        """Obtener texto display para condición de venta"""
        condiciones = {
            "CONTADO": "Contado",
            "CREDITO": "Crédito"
        }
        return condiciones.get(condicion.upper(), condicion)
    
    @staticmethod
    def validate_punto_expedicion(punto: str) -> str:
        """Validar y formatear punto de expedición"""
        if not punto:
            return "001"
        
        # Limpiar y formatear con 3 dígitos
        punto_clean = re.sub(r'[^0-9]', '', punto)
        return punto_clean.zfill(3)
    
    @staticmethod
    def format_currency(amount: Decimal, currency: str = "PYG") -> str:
        """Formatear moneda paraguaya"""
        if currency == "PYG":
            # Formato paraguayo: 1.234.567 Gs.
            return f"{amount:,.0f} Gs.".replace(",", ".")
        elif currency == "USD":
            return f"US$ {amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency}"