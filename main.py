import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar configuración de base de datos unificada
from app.core.database import engine, Base, get_database

# Importar todos los modelos para que las tablas se creen
from app.models import user, customer, product, sales, invoice, deposit, company

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código de inicio
    print("Iniciando el sistema de gestión de ventas...")
    print("Base de datos configurada - usar 'alembic upgrade head' para crear tablas")
    yield
    # Código de limpieza al cerrar
    print("Cerrando el sistema de gestión de ventas...")

# Crear la aplicación FastAPI
app = FastAPI(
    title="Sistema de Gestión de Ventas",
    description="Sistema completo de gestión de ventas con CRM, cotizaciones, facturación e inventario",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS para producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporalmente permitir todos los orígenes para debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar routers de API
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.customers import router as customers_router
from app.api.quotes import router as quotes_router
from app.api.sales_orders import router as sales_orders_router
from app.api.products import router as products_router
from app.api.invoices import router as invoices_router
from app.api.dashboard import router as dashboard_router
from app.api.notifications import router as notifications_router
from app.api.deposits import router as deposits_router
from app.api.company import router as company_router

# Incluir routers
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(customers_router, prefix="/api")
app.include_router(quotes_router, prefix="/api")
app.include_router(sales_orders_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(invoices_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api/dashboard")
app.include_router(notifications_router, prefix="/api/notifications")
app.include_router(deposits_router, prefix="/api")
app.include_router(company_router, prefix="/api")

# Servir archivos estáticos del frontend React
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
# Servir archivos públicos del frontend (vite.svg, favicon, etc.)
app.mount("/public", StaticFiles(directory="frontend/dist"), name="public")

# Ruta de prueba
@app.get("/api")
async def api_info():
    return {
        "message": "Sistema de Gestión de Ventas",
        "version": "1.0.0",
        "status": "active",
        "description": "API para gestión completa de ventas, CRM, inventario y facturación"
    }

# Servir la interfaz React SPA
from fastapi.responses import FileResponse
@app.get("/")
async def main():
    return FileResponse('frontend/dist/index.html')

# Servir rutas de React Router (SPA)
@app.get("/{path:path}")
async def serve_spa(path: str):
    # Para rutas de la SPA, servir index.html
    if path.startswith("api/"):
        # Si es una ruta de API no encontrada, dejar que FastAPI maneje el 404
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Para todas las demás rutas, servir el index.html para que React Router maneje la navegación
    return FileResponse('frontend/dist/index.html')

# Ruta de health check
@app.get("/health")
async def health_check(db: Session = Depends(get_database)):
    try:
        # Verificar conexión a la base de datos
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2025-01-16"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)