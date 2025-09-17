import logging
from datetime import datetime, timedelta
from typing import List
from celery import current_task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import get_database
from app.models import Customer  # Import from models module to ensure all models are registered
from app.core.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    """Servicio para gestionar notificaciones del sistema"""
    
    @staticmethod
    def get_customers_with_expiring_tourism(db: Session, days_ahead: int = 5) -> List[Customer]:
        """
        Obtiene clientes cuyo régimen de turismo vence en los próximos X días
        """
        future_date = datetime.now().date() + timedelta(days=days_ahead)
        
        return db.query(Customer).filter(
            Customer.tourism_regime == True,
            Customer.tourism_regime_expiry.isnot(None),
            Customer.tourism_regime_expiry <= future_date,
            Customer.tourism_regime_expiry >= datetime.now().date()
        ).all()
    
    @staticmethod
    def send_notification(customer: Customer, days_until_expiry: int) -> bool:
        """
        Envía notificación sobre vencimiento de régimen de turismo
        Por ahora registra en logs - puede expandirse a email/SMS
        """
        try:
            message = (
                f"AVISO: Régimen de turismo del cliente '{customer.company_name}' "
                f"(ID: {customer.id}) vence en {days_until_expiry} días "
                f"(Fecha vencimiento: {customer.tourism_regime_expiry})"
            )
            
            logger.warning(f"🚨 NOTIFICACIÓN TURISMO: {message}")
            
            # Aquí se puede expandir para enviar email
            # send_email_notification(customer, message)
            
            return True
            
        except Exception as e:
            logger.error(f"Error enviando notificación para cliente {customer.id}: {str(e)}")
            return False
    
    @staticmethod
    def process_expiry_notifications(db: Session) -> dict:
        """
        Procesa todas las notificaciones de vencimiento
        """
        result = {
            "processed": 0,
            "notifications_sent": 0,
            "errors": 0,
            "customers_notified": []
        }
        
        try:
            # Buscar clientes con régimen próximo a vencer (5 días)
            expiring_customers = NotificationService.get_customers_with_expiring_tourism(db, days_ahead=5)
            
            for customer in expiring_customers:
                result["processed"] += 1
                
                # Calcular días hasta vencimiento
                days_until = (customer.tourism_regime_expiry - datetime.now().date()).days
                
                # Enviar notificación
                if NotificationService.send_notification(customer, days_until):
                    result["notifications_sent"] += 1
                    result["customers_notified"].append({
                        "id": customer.id,
                        "company_name": customer.company_name,
                        "expiry_date": customer.tourism_regime_expiry.isoformat(),
                        "days_until": days_until
                    })
                else:
                    result["errors"] += 1
            
            logger.info(f"Procesamiento completado: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error en proceso de notificaciones: {str(e)}")
            result["errors"] += 1
            return result

@celery_app.task(name="app.services.notification_service.check_tourism_expiry_task")
def check_tourism_expiry_task():
    """
    Task de Celery para verificar vencimientos de régimen de turismo
    Se ejecuta diariamente a las 8:00 AM
    """
    logger.info("🔍 Iniciando verificación de vencimientos de régimen de turismo...")
    
    db = None
    try:
        # Obtener sesión de base de datos
        db_generator = get_database()
        db = next(db_generator)
        
        # Procesar notificaciones
        result = NotificationService.process_expiry_notifications(db)
        
        logger.info(f"✅ Verificación completada: {result}")
        return result
        
    except Exception as e:
        error_msg = f"❌ Error en task de verificación: {str(e)}"
        logger.error(error_msg)
        raise e
    
    finally:
        try:
            if db is not None:
                db.close()
        except:
            pass

# Función para trigger manual (testing/debug)
def trigger_expiry_check_manually():
    """
    Función para ejecutar manualmente la verificación de vencimientos
    Útil para testing y debug
    """
    return check_tourism_expiry_task.delay()  # type: ignore