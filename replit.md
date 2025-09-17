# 🇵🇾 Sistema de Gestión de Ventas - Paraguay

## 📄 Descripción del Proyecto
Sistema completo de gestión de ventas específicamente diseñado para empresas paraguayas. Incluye cumplimiento fiscal paraguayo, gestión de clientes con régimen turístico, facturación con IVA, cotizaciones, inventario y reportes. Totalmente funcional y listo para producción.

## 🚀 Características Principales
- **Cumplimiento Fiscal Paraguayo**: RUC, timbrado, numeración oficial
- **Régimen Turístico**: Gestión automática de exenciones fiscales
- **Facturación con IVA**: Cálculos automáticos (10%, 5%, exento)
- **PDFs Oficiales**: Facturas y cotizaciones con formato paraguayo
- **Dashboard Completo**: Estadísticas y reportes del negocio
- **Autenticación JWT**: Sistema seguro con roles y permisos

## Estado Actual del Proyecto

### ✅ SISTEMA COMPLETAMENTE FUNCIONAL
1. **Arquitectura Base**: FastAPI + React + PostgreSQL completamente configurado y ejecutándose
2. **Base de Datos**: Esquema completo con migraciones aplicadas exitosamente
3. **Autenticación**: Sistema JWT + RBAC funcionando (admin/admin123)
4. **Configuración de Empresa**: Módulo completo con datos fiscales paraguayos
5. **Gestión de Clientes**: Incluye régimen turístico prominente con validaciones
6. **Dashboard Funcional**: Estadísticas reales del negocio con datos paraguayos
7. **Facturación Fiscal**: Cumplimiento total de normativas paraguayas
8. **Documentos PDF**: Generación de cotizaciones y facturas con formato oficial

### 🇵🇾 CARACTERÍSTICAS ESPECÍFICAS DE PARAGUAY
- **Validación RUC**: Algoritmo completo con dígito verificador
- **Timbrado**: Control de numeración fiscal y fechas de vencimiento
- **IVA Paraguayo**: Cálculos automáticos (10%, 5%, exento)
- **Punto de Expedición**: Configuración por empresa
- **Régimen Turístico**: Exenciones fiscales automáticas
- **Numeración Oficial**: Formato 001-0000001 según normativas
- **PDFs Oficiales**: Facturas y cotizaciones con formato paraguayo

## Tecnologías Utilizadas
- **Backend**: FastAPI, SQLAlchemy, Alembic, PostgreSQL
- **Frontend**: React con TypeScript, Vite
- **Autenticación**: JWT con bcrypt
- **Base de Datos**: PostgreSQL
- **Containerización**: Docker & Docker Compose

## Estructura del Proyecto
```
/
├── app/
│   ├── api/         # Endpoints de la API
│   ├── core/        # Configuración y utilidades
│   ├── crud/        # Operaciones de base de datos
│   ├── models/      # Modelos SQLAlchemy
│   └── schemas/     # Esquemas Pydantic
├── frontend/        # Aplicación React
├── alembic/         # Migraciones de base de datos
└── docker-compose.yml
```

## 🛠️ Instalación y Configuración

### Prerrequisitos
- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Redis 7+

### Configuración del Entorno
1. Clonar el repositorio:
```bash
git clone <repository-url>
cd sistema-ventas-paraguay
```

2. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

3. Instalar dependencias del backend:
```bash
pip install -r requirements.txt
# o usar uv:
uv pip install -r pyproject.toml
```

4. Instalar dependencias del frontend:
```bash
cd frontend
npm install
```

### 🚀 Ejecución

#### Con Docker (Recomendado)
```bash
docker-compose up --build
```
La aplicación estará disponible en: http://localhost:5000

#### Sin Docker
1. Configurar base de datos:
```bash
alembic upgrade head
```

2. Ejecutar servicios en terminales separadas:
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Backend API
python main.py

# Terminal 3: Frontend (desarrollo)
cd frontend && npm run dev

# Terminal 4: Celery Worker (opcional)
celery -A app.core.celery_app worker --loglevel=info

# Terminal 5: Celery Beat (opcional)
celery -A app.core.celery_app beat --loglevel=info
```

## 📋 APIs Disponibles

### Autenticación
- `POST /api/auth/register` - Registro de usuario
- `POST /api/auth/login` - Inicio de sesión  
- `GET /api/auth/me` - Obtener perfil del usuario
- `POST /api/auth/refresh` - Renovar token

### Gestión de Empresa
- `GET /api/company/settings` - Configuraciones de la empresa
- `PUT /api/company/settings` - Actualizar configuraciones

### Clientes
- `GET /api/customers` - Listar clientes
- `POST /api/customers` - Crear cliente
- `GET /api/customers/{id}` - Obtener cliente
- `PUT /api/customers/{id}` - Actualizar cliente
- `DELETE /api/customers/{id}` - Eliminar cliente

### Productos
- `GET /api/products` - Listar productos
- `POST /api/products` - Crear producto
- `GET /api/products/{id}` - Obtener producto
- `PUT /api/products/{id}` - Actualizar producto

### Cotizaciones
- `GET /api/quotes` - Listar cotizaciones
- `POST /api/quotes` - Crear cotización
- `GET /api/quotes/{id}/pdf` - Generar PDF de cotización

### Facturas
- `GET /api/invoices` - Listar facturas
- `POST /api/invoices` - Crear factura
- `GET /api/invoices/{id}/pdf` - Generar PDF de factura

### Dashboard
- `GET /api/dashboard/stats` - Estadísticas generales
- `GET /api/dashboard/revenue` - Ingresos por período

## 🔐 Credenciales por Defecto
- **Usuario**: admin
- **Contraseña**: admin123

## 🤝 Contribución
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear un Pull Request

## 📄 Licencia
Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para detalles.

## 📞 Soporte
Para soporte técnico o consultas sobre el sistema, contacta al desarrollador.

---
**Desarrollado específicamente para empresas paraguayas** 🇵🇾