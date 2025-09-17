from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from enum import Enum
from decimal import Decimal
from datetime import date

class CurrencyType(str, Enum):
    PYG = "PYG"  # Guaraníes paraguayos
    USD = "USD"  # Dólares americanos

class PrintFormat(str, Enum):
    A4 = "A4"
    TICKET = "ticket"

class CompanySettingsBase(BaseModel):
    # DATOS BÁSICOS DE LA EMPRESA
    razon_social: str
    nombre_comercial: Optional[str] = None
    
    # DATOS FISCALES ESPECÍFICOS PARA PARAGUAY
    ruc: str
    timbrado: str
    timbrado_fecha_vencimiento: Optional[date] = None
    punto_expedicion: str = "001"
    dv_ruc: Optional[str] = None
    
    # DATOS DE CONTACTO
    direccion: str
    ciudad: str = "Asunción"
    departamento: str = "Central"
    codigo_postal: Optional[str] = None
    telefono: Optional[str] = None
    celular: Optional[str] = None
    email: Optional[EmailStr] = None
    sitio_web: Optional[str] = None
    
    # CONFIGURACIÓN MONETARIA
    moneda_defecto: CurrencyType = CurrencyType.PYG
    
    # CONFIGURACIÓN DE IVA PARA PARAGUAY
    iva_10_porciento: Decimal = Decimal("10.00")
    iva_5_porciento: Decimal = Decimal("5.00")
    iva_exento: bool = False
    
    # CONFIGURACIÓN DE NUMERACIÓN AUTOMÁTICA
    numeracion_facturas_inicio: int = 1
    numeracion_facturas_actual: int = 1
    numeracion_cotizaciones_inicio: int = 1
    numeracion_cotizaciones_actual: int = 1
    
    # CONFIGURACIÓN DE IMPRESIÓN
    formato_impresion: PrintFormat = PrintFormat.A4
    
    # ARCHIVOS Y MULTIMEDIA
    logo_empresa: Optional[str] = None
    firma_digital: Optional[str] = None
    
    # CONFIGURACIÓN ESPECÍFICA PARA PARAGUAY
    regimen_tributario: str = "GENERAL"
    contribuyente_iva: bool = True
    
    # INFORMACIÓN ADICIONAL
    actividad_economica: Optional[str] = None
    sector_economico: Optional[str] = None
    notas_adicionales: Optional[str] = None
    
    # CONFIGURACIÓN DE SISTEMA
    is_active: bool = True
    configuracion_completa: bool = False

    @field_validator('ruc')
    @classmethod
    def validate_ruc(cls, v):
        """Validar formato básico de RUC paraguayo"""
        if not v:
            raise ValueError('RUC es obligatorio')
        
        # Eliminar espacios y guiones para validación
        ruc_clean = v.replace('-', '').replace(' ', '')
        
        # Verificar que sea numérico y tenga la longitud correcta
        if not ruc_clean.isdigit():
            raise ValueError('RUC debe contener solo números')
        
        if len(ruc_clean) < 6 or len(ruc_clean) > 10:
            raise ValueError('RUC debe tener entre 6 y 10 dígitos')
            
        return v
    
    @field_validator('timbrado')
    @classmethod
    def validate_timbrado(cls, v):
        """Validar formato básico de timbrado"""
        if not v:
            raise ValueError('Timbrado es obligatorio')
        
        timbrado_clean = v.replace('-', '').replace(' ', '')
        
        if not timbrado_clean.isdigit():
            raise ValueError('Timbrado debe contener solo números')
        
        if len(timbrado_clean) < 8:
            raise ValueError('Timbrado debe tener al menos 8 dígitos')
            
        return v
    
    @field_validator('punto_expedicion')
    @classmethod
    def validate_punto_expedicion(cls, v):
        """Validar formato de punto de expedición"""
        if not v:
            return "001"
        
        # Asegurar que tenga 3 dígitos con ceros a la izquierda
        return v.zfill(3)

class CompanySettingsCreate(CompanySettingsBase):
    pass

class CompanySettingsUpdate(BaseModel):
    # Todos los campos opcionales para actualización
    razon_social: Optional[str] = None
    nombre_comercial: Optional[str] = None
    ruc: Optional[str] = None
    timbrado: Optional[str] = None
    timbrado_fecha_vencimiento: Optional[date] = None
    punto_expedicion: Optional[str] = None
    dv_ruc: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    codigo_postal: Optional[str] = None
    telefono: Optional[str] = None
    celular: Optional[str] = None
    email: Optional[EmailStr] = None
    sitio_web: Optional[str] = None
    moneda_defecto: Optional[CurrencyType] = None
    iva_10_porciento: Optional[Decimal] = None
    iva_5_porciento: Optional[Decimal] = None
    iva_exento: Optional[bool] = None
    numeracion_facturas_inicio: Optional[int] = None
    numeracion_facturas_actual: Optional[int] = None
    numeracion_cotizaciones_inicio: Optional[int] = None
    numeracion_cotizaciones_actual: Optional[int] = None
    formato_impresion: Optional[PrintFormat] = None
    logo_empresa: Optional[str] = None
    firma_digital: Optional[str] = None
    regimen_tributario: Optional[str] = None
    contribuyente_iva: Optional[bool] = None
    actividad_economica: Optional[str] = None
    sector_economico: Optional[str] = None
    notas_adicionales: Optional[str] = None
    is_active: Optional[bool] = None
    configuracion_completa: Optional[bool] = None

    # Aplicar las mismas validaciones cuando se actualizan los campos
    @field_validator('ruc')
    @classmethod
    def validate_ruc(cls, v):
        if v is None:
            return v
        return CompanySettingsBase.validate_ruc(v)
    
    @field_validator('timbrado')
    @classmethod
    def validate_timbrado(cls, v):
        if v is None:
            return v
        return CompanySettingsBase.validate_timbrado(v)
    
    @field_validator('punto_expedicion')
    @classmethod
    def validate_punto_expedicion(cls, v):
        if v is None:
            return v
        return CompanySettingsBase.validate_punto_expedicion(v)

class CompanySettings(CompanySettingsBase):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    model_config = {"from_attributes": True}

class CompanySettingsPublic(BaseModel):
    """Configuración pública de la empresa (para mostrar en facturas, etc.)"""
    id: int
    razon_social: str
    nombre_comercial: Optional[str] = None
    ruc: str
    direccion: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    logo_empresa: Optional[str] = None
    moneda_defecto: CurrencyType
    
    model_config = {"from_attributes": True}