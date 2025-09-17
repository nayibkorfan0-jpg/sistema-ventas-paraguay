from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, Date
from sqlalchemy.types import Numeric
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class CurrencyType(enum.Enum):
    PYG = "PYG"  # Guaraníes paraguayos
    USD = "USD"  # Dólares americanos

class PrintFormat(enum.Enum):
    A4 = "A4"
    TICKET = "ticket"

class CompanySettings(Base):
    __tablename__ = "company_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # DATOS BÁSICOS DE LA EMPRESA
    razon_social = Column(String(200), nullable=False, comment="Razón social de la empresa")
    nombre_comercial = Column(String(200), nullable=True, comment="Nombre comercial")
    
    # DATOS FISCALES ESPECÍFICOS PARA PARAGUAY
    ruc = Column(String(20), nullable=False, unique=True, comment="RUC paraguayo (ej: 80012345-1)")
    timbrado = Column(String(20), nullable=False, comment="Número de timbrado fiscal")
    timbrado_fecha_vencimiento = Column(Date, nullable=True, comment="Fecha de vencimiento del timbrado")
    punto_expedicion = Column(String(10), nullable=False, default="001", comment="Punto de expedición")
    dv_ruc = Column(String(2), nullable=True, comment="Dígito verificador del RUC")
    
    # DATOS DE CONTACTO
    direccion = Column(Text, nullable=False, comment="Dirección completa de la empresa")
    ciudad = Column(String(100), nullable=False, default="Asunción", comment="Ciudad")
    departamento = Column(String(100), nullable=False, default="Central", comment="Departamento/Estado")
    codigo_postal = Column(String(10), nullable=True, comment="Código postal")
    telefono = Column(String(20), nullable=True, comment="Teléfono fijo")
    celular = Column(String(20), nullable=True, comment="Teléfono celular")
    email = Column(String(100), nullable=True, comment="Email principal")
    sitio_web = Column(String(200), nullable=True, comment="Sitio web de la empresa")
    
    # CONFIGURACIÓN MONETARIA
    moneda_defecto = Column(
        PGEnum(
            CurrencyType,
            name="currency_type",
            values_callable=lambda e: [m.value for m in e],
            create_type=False,
        ),
        default=CurrencyType.PYG,
        nullable=False,
        comment="Moneda por defecto"
    )
    
    # CONFIGURACIÓN DE IVA PARA PARAGUAY
    iva_10_porciento = Column(Numeric(5, 2), default=10.00, nullable=False, comment="Tasa IVA 10%")
    iva_5_porciento = Column(Numeric(5, 2), default=5.00, nullable=False, comment="Tasa IVA 5%")
    iva_exento = Column(Boolean, default=False, comment="Empresa exenta de IVA")
    
    # CONFIGURACIÓN DE NUMERACIÓN AUTOMÁTICA
    numeracion_facturas_inicio = Column(Integer, default=1, nullable=False, comment="Número inicial de facturas")
    numeracion_facturas_actual = Column(Integer, default=1, nullable=False, comment="Número actual de facturas")
    numeracion_cotizaciones_inicio = Column(Integer, default=1, nullable=False, comment="Número inicial de cotizaciones")
    numeracion_cotizaciones_actual = Column(Integer, default=1, nullable=False, comment="Número actual de cotizaciones")
    
    # CONFIGURACIÓN DE IMPRESIÓN
    formato_impresion = Column(
        PGEnum(
            PrintFormat,
            name="print_format",
            values_callable=lambda e: [m.value for m in e],
            create_type=False,
        ),
        default=PrintFormat.A4,
        nullable=False,
        comment="Formato de impresión por defecto"
    )
    
    # ARCHIVOS Y MULTIMEDIA
    logo_empresa = Column(String(500), nullable=True, comment="Path del logo de la empresa")
    firma_digital = Column(String(500), nullable=True, comment="Path de la firma digital")
    
    # CONFIGURACIÓN ESPECÍFICA PARA PARAGUAY
    regimen_tributario = Column(String(50), default="GENERAL", nullable=False, comment="Régimen tributario")
    contribuyente_iva = Column(Boolean, default=True, nullable=False, comment="Es contribuyente de IVA")
    
    # INFORMACIÓN ADICIONAL
    actividad_economica = Column(String(200), nullable=True, comment="Actividad económica principal")
    sector_economico = Column(String(100), nullable=True, comment="Sector económico")
    notas_adicionales = Column(Text, nullable=True, comment="Notas y observaciones adicionales")
    
    # CONFIGURACIÓN DE SISTEMA
    is_active = Column(Boolean, default=True, nullable=False)
    configuracion_completa = Column(Boolean, default=False, nullable=False, comment="Indica si la configuración está completa")
    
    # TIMESTAMPS
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<CompanySettings(razon_social='{self.razon_social}', ruc='{self.ruc}')>"