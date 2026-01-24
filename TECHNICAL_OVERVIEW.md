# 🏢 CondoAdmin Pro - Resumen Técnico del Sistema

## 📊 Visión General

Sistema integral de administración de condominios desarrollado desde cero con arquitectura MVC, control de permisos granular y diseño responsive.

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTACIÓN (Frontend)               │
│  ┌──────────────┬───────────────┬──────────────────┐    │
│  │  Templates   │   Tailwind    │   JavaScript     │    │
│  │    (Jinja2)  │      CSS      │  (Alpine.js)     │    │
│  └──────────────┴───────────────┴──────────────────┘    │
├─────────────────────────────────────────────────────────┤
│                     LÓGICA (Backend)                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │             Flask Application                     │   │
│  │  ┌────────────────────────────────────────────┐  │   │
│  │  │  Blueprints (Rutas)                         │  │   │
│  │  │  • auth      • dashboard  • roles           │  │   │
│  │  │  • bookings  • parking    • financials      │  │   │
│  │  │  • announcements                            │  │   │
│  │  └────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────┐  │   │
│  │  │  Sistema de Permisos                        │  │   │
│  │  │  • Decoradores  • Middleware  • Roles       │  │   │
│  │  └────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                      DATOS (Database)                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │            SQLAlchemy ORM                         │   │
│  │  ┌──────────┬──────────┬──────────┬──────────┐   │   │
│  │  │  Users   │ Bookings │ Parking  │Financial │   │   │
│  │  │  Roles   │Facilities│   Logs   │  Trans.  │   │   │
│  │  │ Modules  │          │          │Announce. │   │   │
│  │  └──────────┴──────────┴──────────┴──────────┘   │   │
│  │              SQLite / PostgreSQL / MySQL          │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🔐 Sistema de Permisos

### Matriz de Permisos por Rol

| Módulo              | Super Admin | Administrador | Guardia | Directiva | Residente |
|---------------------|-------------|---------------|---------|-----------|-----------|
| **Roles/Usuarios**  | ✏️ (2)      | 👁️ (1)       | ❌ (0)  | 👁️ (1)   | ❌ (0)    |
| **Reservas**        | ✏️ (2)      | ✏️ (2)        | 👁️ (1) | 👁️ (1)   | ✏️ (2)    |
| **Estacionamiento** | ✏️ (2)      | ✏️ (2)        | ✏️ (2)  | 👁️ (1)   | 👁️ (1)    |
| **Finanzas**        | ✏️ (2)      | ✏️ (2)        | ❌ (0)  | ✏️ (2)    | 👁️ (1)    |
| **Comunicados**     | ✏️ (2)      | ✏️ (2)        | 👁️ (1) | ✏️ (2)    | 👁️ (1)    |

**Leyenda:**
- ❌ (0): Sin acceso
- 👁️ (1): Solo lectura
- ✏️ (2): Lectura y escritura

### Implementación en Código

```python
# Decorador de permisos
@bp.route('/users')
@login_required
@require_permission('roles', level=1)  # Requiere nivel 1 (lectura)
def users():
    # Vista de usuarios
    pass

# Verificación en templates
{% if current_user.can_write('bookings') %}
    <button>Crear Reserva</button>
{% endif %}

# Verificación en lógica
if current_user.has_permission('financials', 2):
    # Permitir crear transacción
```

---

## 📦 Módulos del Sistema

### 1. 🔐 Gestión de Roles y Permisos

**Entidades:**
- `User`: Usuarios del sistema
- `Role`: Roles predefinidos
- `Module`: Módulos del sistema
- `ModulePermission`: Permisos por rol y módulo

**Funcionalidades:**
- ✅ Crear/editar usuarios
- ✅ Asignar roles
- ✅ Configurar permisos granulares
- ✅ Activar/desactivar usuarios
- ✅ Historial de accesos

### 2. 📅 Reserva de Espacios Comunes

**Entidades:**
- `Facility`: Instalaciones (Quincho, Piscina, etc.)
- `Booking`: Reservas

**Funcionalidades:**
- ✅ Calendario interactivo
- ✅ Verificación de disponibilidad
- ✅ Sistema de aprobaciones
- ✅ Cancelación de reservas
- ✅ Conflicto de horarios

**Reglas de Negocio:**
```python
# Verificar disponibilidad
def is_available(date, start_time, end_time):
    - No solapar con otras reservas
    - Respetar anticipación mínima
    - Validar duración máxima
    - Verificar si requiere aprobación
```

### 3. 🚗 Estado de Estacionamientos

**Entidades:**
- `ParkingSpot`: Espacios de estacionamiento
- `ParkingLog`: Historial de cambios

**Funcionalidades:**
- ✅ Mapa visual con colores
- ✅ Asignación a usuarios
- ✅ Registro de vehículos
- ✅ Historial completo
- ✅ Filtros por piso/estado

**Estados:**
- 🟢 `available`: Disponible
- 🔴 `occupied`: Ocupado
- 🔵 `reserved`: Reservado
- 🟡 `maintenance`: Mantenimiento

### 4. 💰 Cuentas y Servicios Pagados

**Entidades:**
- `FinancialAccount`: Cuenta por unidad
- `FinancialTransaction`: Transacciones
- `ServicePayment`: Pagos de servicios

**Funcionalidades:**
- ✅ Balance automático
- ✅ Registro de cargos/pagos
- ✅ Cuentas críticas
- ✅ Servicios del edificio
- ✅ Estadísticas mensuales

**Flujo de Transacciones:**
```
1. Crear cargo (charge) → total_owed += amount
2. Registrar pago (payment) → total_paid += amount
3. Calcular balance → total_paid - total_owed
4. Actualizar estado → current/overdue/critical
```

### 5. 📢 Comunicados Oficiales

**Entidades:**
- `Announcement`: Anuncios
- `AnnouncementAcknowledgment`: Confirmaciones de lectura
- `AnnouncementComment`: Comentarios (opcional)

**Funcionalidades:**
- ✅ Prioridades (normal, urgente, informativo)
- ✅ Categorías
- ✅ Confirmación de lectura
- ✅ Fechas de expiración
- ✅ Estadísticas de lectura

---

## 🗄️ Modelo de Base de Datos

### Diagrama Simplificado

```
users ─────┬───── roles
           │         │
           │         └───── module_permissions ───── modules
           │
           ├───── bookings ───── facilities
           │
           ├───── parking_spots
           │         │
           │         └───── parking_logs
           │
           ├───── financial_accounts
           │         │
           │         └───── financial_transactions
           │
           └───── announcements
                     │
                     └───── announcement_acknowledgments
```

### Tablas Principales

| Tabla | Registros | Relaciones |
|-------|-----------|------------|
| users | N usuarios | → roles (N:1) |
| roles | 5 predefinidos | ← users, → module_permissions |
| modules | 5 módulos | ← module_permissions |
| facilities | 4+ instalaciones | ← bookings |
| parking_spots | 40+ espacios | → users, ← parking_logs |
| financial_accounts | 20+ cuentas | → users, ← transactions |
| announcements | N comunicados | → users (author) |

---

## 🎨 Stack Tecnológico

### Backend
- **Flask 3.0.0**: Framework web minimalista
- **SQLAlchemy**: ORM potente y flexible
- **Flask-Login**: Gestión de sesiones
- **Flask-Migrate**: Migraciones automáticas
- **Werkzeug**: Hashing de contraseñas

### Frontend
- **Tailwind CSS 3.x**: Utility-first CSS
- **Alpine.js**: Reactividad ligera
- **Font Awesome 6.4**: Iconografía
- **Jinja2**: Motor de templates

### Base de Datos
- **SQLite** (desarrollo)
- Compatible con PostgreSQL/MySQL (producción)

---

## 🔄 Flujos de Trabajo Clave

### 1. Autenticación
```
Usuario → Login Form → Flask-Login → Verificar Password
                                        ↓
                                   ¿Válido?
                                        ↓
                                   Yes ─→ Crear Sesión → Dashboard
                                   No ──→ Error → Login Form
```

### 2. Crear Reserva
```
Usuario → Seleccionar Instalación → Elegir Fecha/Hora
                                          ↓
                                   Verificar Disponibilidad
                                          ↓
                                    ¿Disponible?
                                          ↓
                              Yes ────────┴──────── No
                               ↓                     ↓
                        Crear Reserva          Mostrar Error
                               ↓
                     ¿Requiere Aprobación?
                          ↓         ↓
                        Yes        No
                          ↓         ↓
                    status=pending  status=approved
```

### 3. Asignar Estacionamiento
```
Admin → Ver Mapa → Clic en Espacio Disponible
                            ↓
                    Seleccionar Usuario
                            ↓
                    Registrar Vehículo
                            ↓
                    spot.assign_to_user()
                            ↓
                    Crear Parking Log
                            ↓
                    Actualizar Mapa
```

---

## 📈 Estadísticas del Proyecto

### Código
- **Líneas de Código**: ~8,000+
- **Archivos Python**: 15+
- **Templates HTML**: 10+
- **Modelos de Datos**: 12 tablas
- **Rutas/Endpoints**: 40+

### Funcionalidades
- **5 Módulos** completamente funcionales
- **5 Roles** predefinidos
- **3 Niveles** de permisos
- **12 Tablas** de base de datos
- **100% Responsive** design

---

## 🚀 Deployment Checklist

### Pre-producción
- [ ] Cambiar `SECRET_KEY` en `.env`
- [ ] Configurar base de datos PostgreSQL
- [ ] Cambiar contraseña de admin
- [ ] Configurar backups automáticos
- [ ] Activar HTTPS
- [ ] Configurar emails (opcional)

### Servidor
- [ ] Instalar Gunicorn: `pip install gunicorn`
- [ ] Configurar NGINX como reverse proxy
- [ ] Configurar SSL con Let's Encrypt
- [ ] Configurar logs de producción
- [ ] Configurar monitoring

### Comando de Producción
```bash
gunicorn -w 4 -b 0.0.0.0:8000 --access-logfile - --error-logfile - run:app
```

---

## 📚 Recursos y Documentación

### Documentación Oficial
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Alpine.js](https://alpinejs.dev/)

### Archivos del Proyecto
- `README.md`: Documentación completa
- `QUICKSTART.md`: Guía de inicio rápido
- `config.py`: Configuración de la aplicación
- `requirements.txt`: Dependencias Python

---

## 💡 Mejoras Futuras Sugeridas

### Corto Plazo
1. Dashboard con gráficos (Chart.js)
2. Exportar reportes a PDF
3. Notificaciones por email
4. Búsqueda avanzada

### Mediano Plazo
5. API REST para app móvil
6. Sistema de tickets/reclamos
7. Calendario de mantenimiento
8. Galería de fotos

### Largo Plazo
9. Integración con pasarelas de pago
10. Chat entre residentes
11. Control de acceso IoT
12. App móvil nativa

---

**Desarrollado con ❤️ para la gestión eficiente de condominios**
*Sistema completo, escalable y fácil de mantener*
