# 🏢 CondoAdmin Pro - Sistema de Administración de Condominios

Sistema completo de gestión de condominios desarrollado con **Flask**, **Python**, **JavaScript**, **Tailwind CSS** y **SQLite**.

## 📋 Características Principales

### 🔐 Sistema de Roles y Permisos
- **5 roles predefinidos**: Super Admin, Administrador, Guardia de Seguridad, Miembro de Directiva, Residente
- **Permisos granulares por módulo** con 3 niveles:
  - **Nivel 0**: Sin acceso
  - **Nivel 1**: Solo lectura
  - **Nivel 2**: Lectura y escritura
- Gestión completa de usuarios y asignación de roles

### 📅 Reserva de Espacios Comunes
- Calendario interactivo para gestionar reservas
- 4 instalaciones predefinidas: Quincho, Piscina, Gimnasio, Sala de Eventos
- Sistema de aprobaciones configurable
- Verificación automática de disponibilidad

### 🚗 Gestión de Estacionamientos
- Mapa visual con códigos de color por estado
- Estados: Disponible, Ocupado, Reservado, Mantenimiento
- Asignación de espacios a usuarios
- Registro de vehículos (patente, marca, modelo, color)
- Historial completo de cambios

### 💰 Control Financiero
- Cuentas por unidad/departamento
- Registro de cargos y pagos
- Balance automático y estados de cuenta
- Gestión de servicios del edificio
- Estadísticas de recaudación mensual
- Identificación de cuentas críticas

### 📢 Comunicados Oficiales
- Sistema de anuncios con prioridades (Normal, Urgente, Informativo)
- Categorías: Mantenimiento, Evento, Aviso, Emergencia
- Confirmaciones de lectura
- Fechas de expiración opcionales

## 🛠️ Tecnologías Utilizadas

### Backend
- **Flask 3.0.0**: Framework web
- **SQLAlchemy**: ORM para base de datos
- **Flask-Login**: Gestión de sesiones
- **Flask-Migrate**: Migraciones de base de datos
- **SQLite**: Base de datos (fácilmente migrable a PostgreSQL/MySQL)

### Frontend
- **Tailwind CSS**: Framework CSS moderno
- **Alpine.js**: Framework JavaScript reactivo
- **Font Awesome**: Iconografía
- **Vanilla JavaScript**: Interactividad personalizada

## 📦 Instalación

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
```bash
cd condo_admin_system
```

2. **Crear entorno virtual**
```bash
python -m venv venv

# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env y configurar:
# - SECRET_KEY (clave secreta para sesiones)
# - DATABASE_URL (opcional, por defecto usa SQLite)
```

5. **Inicializar base de datos**
```bash
# Crear tablas y datos iniciales
flask --app run.py init-db

# O simplemente ejecutar la aplicación (creará automáticamente)
python run.py
```

## 🚀 Ejecución

### Modo Desarrollo
```bash
python run.py
```

La aplicación estará disponible en: `http://localhost:5000`

### Credenciales por Defecto
- **Email**: `admin@condoadmin.com`
- **Contraseña**: `admin123`

⚠️ **IMPORTANTE**: Cambiar estas credenciales en producción.

## 📁 Estructura del Proyecto

```
condo_admin_system/
│
├── app/
│   ├── __init__.py          # Factory de la aplicación
│   ├── models/              # Modelos de base de datos
│   │   ├── __init__.py
│   │   ├── user.py          # Usuario, Rol, Módulo, Permisos
│   │   ├── booking.py       # Instalaciones y Reservas
│   │   ├── parking.py       # Estacionamientos
│   │   ├── financial.py     # Finanzas
│   │   └── announcement.py  # Comunicados
│   │
│   ├── routes/              # Rutas (Blueprints)
│   │   ├── __init__.py
│   │   ├── auth.py          # Autenticación
│   │   ├── dashboard.py     # Dashboard principal
│   │   ├── roles.py         # Gestión de roles
│   │   ├── bookings.py      # Reservas
│   │   ├── parking.py       # Estacionamientos
│   │   ├── financials.py    # Finanzas
│   │   └── announcements.py # Comunicados
│   │
│   ├── templates/           # Templates HTML
│   │   ├── layouts/
│   │   │   └── base.html    # Template base
│   │   ├── auth/
│   │   │   └── login.html
│   │   ├── dashboard/
│   │   │   └── index.html
│   │   ├── roles/
│   │   │   └── users.html
│   │   └── ...
│   │
│   └── static/              # Archivos estáticos
│       ├── css/
│       ├── js/
│       └── images/
│
├── config.py                # Configuración
├── run.py                   # Punto de entrada
├── requirements.txt         # Dependencias
├── .env.example            # Ejemplo de variables de entorno
└── README.md               # Este archivo
```

## 🔧 Configuración Avanzada

### Cambiar Base de Datos

Por defecto usa SQLite. Para usar PostgreSQL o MySQL:

```python
# En .env
DATABASE_URL=postgresql://usuario:password@localhost/condoadmin
# o
DATABASE_URL=mysql://usuario:password@localhost/condoadmin
```

### Agregar Nuevos Módulos

1. Crear modelo en `app/models/`
2. Crear rutas en `app/routes/`
3. Registrar blueprint en `app/__init__.py`
4. Crear templates en `app/templates/`
5. Agregar módulo a la tabla `modules` en la base de datos

## 📊 Módulos del Sistema

### 1. Gestión de Roles y Permisos
- **Ruta**: `/roles`
- **Permisos**: Configurable por rol
- **Funciones**:
  - Listar usuarios y roles
  - Crear/editar usuarios
  - Modificar permisos por rol
  - Activar/desactivar usuarios

### 2. Reserva de Espacios Comunes
- **Ruta**: `/bookings`
- **Permisos**: Configurable por rol
- **Funciones**:
  - Calendario de reservas
  - Crear nueva reserva
  - Aprobar/rechazar reservas
  - Cancelar reservas
  - Verificación de disponibilidad

### 3. Estado de Estacionamientos
- **Ruta**: `/parking`
- **Permisos**: Configurable por rol
- **Funciones**:
  - Mapa visual de espacios
  - Asignar/liberar espacios
  - Registro de vehículos
  - Historial de cambios
  - Filtros por piso y estado

### 4. Cuentas y Servicios Pagados
- **Ruta**: `/financials`
- **Permisos**: Configurable por rol
- **Funciones**:
  - Dashboard financiero
  - Cuentas por unidad
  - Registro de cargos y pagos
  - Gestión de servicios
  - Reportes de recaudación

### 5. Comunicados Oficiales
- **Ruta**: `/announcements`
- **Permisos**: Configurable por rol
- **Funciones**:
  - Crear/editar anuncios
  - Prioridades y categorías
  - Confirmaciones de lectura
  - Filtros avanzados

## 🎨 Personalización

### Modificar Colores y Estilos

El sistema usa Tailwind CSS. Para personalizar:

1. Editar clases en los templates HTML
2. Agregar CSS personalizado en `app/static/css/`

### Agregar Nuevas Instalaciones

```python
# En Flask shell o script
from app.models import Facility
from app import db

facility = Facility(
    name='Nueva Instalación',
    description='Descripción',
    capacity=20,
    color='#FF5733',
    icon='🏀',
    requires_approval=True
)
db.session.add(facility)
db.session.commit()
```

## 🔒 Seguridad

- Contraseñas hasheadas con Werkzeug
- Protección CSRF en formularios
- Sesiones seguras con cookies HTTP-only
- Control de permisos por módulo
- Validación de datos en servidor

## 📝 Comandos Útiles

```bash
# Inicializar base de datos con datos de ejemplo
flask --app run.py init-db

# Entrar a shell de Flask
flask --app run.py shell

# Crear migración
flask --app run.py db migrate -m "descripción"

# Aplicar migración
flask --app run.py db upgrade
```

## 🐛 Solución de Problemas

### Error: "No module named 'flask'"
```bash
pip install -r requirements.txt
```

### Error de base de datos
```bash
# Eliminar base de datos y recrear
rm condo_admin.db
python run.py
```

### Puerto 5000 ocupado
```python
# En run.py, cambiar:
app.run(debug=True, host='0.0.0.0', port=8000)
```

## 📈 Próximas Mejoras

- [ ] Dashboard con gráficos interactivos (Chart.js)
- [ ] Exportación de reportes a PDF/Excel
- [ ] Sistema de notificaciones por email
- [ ] API REST para integración móvil
- [ ] Módulo de mantenimiento preventivo
- [ ] Sistema de tickets/reclamos
- [ ] Galería de fotos del condominio
- [ ] Chat interno entre residentes

## 👥 Roles Predefinidos

| Rol | Roles | Reservas | Estacionamiento | Finanzas | Comunicados |
|-----|-------|----------|-----------------|----------|-------------|
| Super Admin | 2 | 2 | 2 | 2 | 2 |
| Administrador | 1 | 2 | 2 | 2 | 2 |
| Guardia | 0 | 1 | 2 | 0 | 1 |
| Directiva | 1 | 1 | 1 | 2 | 2 |
| Residente | 0 | 2 | 1 | 1 | 1 |

**Leyenda**: 0 = Sin acceso, 1 = Lectura, 2 = Lectura/Escritura

## 📞 Soporte

Para dudas o problemas, por favor crea un issue en el repositorio.

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

**Desarrollado con ❤️ para la gestión eficiente de condominios**
