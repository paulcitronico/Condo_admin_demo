# 🚀 Guía de Inicio Rápido - CondoAdmin Pro

## ⚡ Instalación Express (5 minutos)

### 1. Preparar Entorno
```bash
# Descomprimir proyecto
tar -xzf condo_admin_system.tar.gz
cd condo_admin_system

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar (Opcional)
```bash
# Copiar configuración de ejemplo
cp .env.example .env

# Editar .env si deseas personalizar
# Por defecto funciona sin modificaciones
```

### 3. Iniciar Aplicación
```bash
python run.py
```

### 4. Acceder al Sistema
- **URL**: http://localhost:5000
- **Usuario**: admin@condoadmin.com
- **Contraseña**: admin123

## 📋 Datos de Ejemplo

Al iniciar por primera vez, el sistema crea automáticamente:
- ✅ 5 roles predefinidos con permisos configurados
- ✅ Usuario administrador
- ✅ 4 instalaciones (Quincho, Piscina, Gimnasio, Sala de Eventos)
- ✅ 40 espacios de estacionamiento (2 pisos, 2 sectores)
- ✅ 20 cuentas financieras
- ✅ Anuncio de bienvenida

### Agregar Más Datos de Ejemplo
```bash
flask --app run.py init-db
```

## 🎯 Primeros Pasos

### 1. Explorar el Dashboard
- Ve a `http://localhost:5000/dashboard`
- Observa las estadísticas generales
- Navega por los diferentes módulos

### 2. Crear un Usuario
1. Ve a **Roles** → **Usuarios**
2. Click en "Añadir Usuario"
3. Llena el formulario
4. Selecciona un rol
5. Guarda

### 3. Hacer una Reserva
1. Ve a **Reservas**
2. Click en "Nueva Reserva"
3. Selecciona instalación, fecha y hora
4. Guarda

### 4. Asignar un Estacionamiento
1. Ve a **Estacionamiento**
2. Click en un espacio disponible (verde)
3. Selecciona usuario
4. Registra datos del vehículo
5. Guarda

### 5. Crear un Comunicado
1. Ve a **Comunicados**
2. Click en "Crear Anuncio"
3. Llena título y contenido
4. Selecciona prioridad
5. Publica

## 🔧 Comandos Útiles

```bash
# Ver todos los usuarios en la consola Python
flask --app run.py shell
>>> from app.models import User
>>> User.query.all()

# Crear usuario desde línea de comandos
flask --app run.py shell
>>> from app import db
>>> from app.models import User, Role
>>> role = Role.query.filter_by(name='resident').first()
>>> user = User(email='nuevo@ejemplo.com', username='nuevo', 
...             first_name='Nuevo', last_name='Usuario', role_id=role.id)
>>> user.set_password('password123')
>>> db.session.add(user)
>>> db.session.commit()

# Resetear base de datos
rm condo_admin.db
python run.py
```

## 🎨 Personalización Rápida

### Cambiar Logo/Nombre
Edita `app/templates/layouts/base.html`:
```html
<span class="text-white text-xl font-bold">
    <i class="fas fa-building"></i> TU NOMBRE AQUÍ
</span>
```

### Cambiar Colores
El sistema usa Tailwind CSS. Busca clases como:
- `bg-blue-600` → color de fondo azul
- `text-red-600` → color de texto rojo
- `border-green-200` → borde verde

Reemplázalas por otros colores de Tailwind.

### Agregar Campo a Usuario
1. Edita `app/models/user.py`
2. Agrega nueva columna: `telefono = db.Column(db.String(20))`
3. Reinicia la aplicación

## 🔍 Estructura de Permisos

### Niveles de Acceso
- **0**: Sin acceso al módulo
- **1**: Solo lectura (ver información)
- **2**: Lectura y escritura (crear, editar, eliminar)

### Verificar Permisos en Código
```python
# En una vista
if current_user.can_read('bookings'):
    # Mostrar reservas
    
if current_user.can_write('financials'):
    # Permitir crear transacciones
```

### Modificar Permisos de un Rol
```bash
flask --app run.py shell
>>> from app.models import Role, Module, ModulePermission
>>> from app import db
>>> role = Role.query.filter_by(name='resident').first()
>>> module = Module.query.filter_by(name='parking').first()
>>> perm = ModulePermission.query.filter_by(role_id=role.id, module_id=module.id).first()
>>> perm.permission_level = 2  # Dar acceso de escritura
>>> db.session.commit()
```

## 🚨 Solución de Problemas Comunes

### "Address already in use"
El puerto 5000 está ocupado. Cambia en `run.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8000)
```

### "ModuleNotFoundError: No module named 'flask'"
No activaste el entorno virtual:
```bash
source venv/bin/activate
```

### Olvidé la contraseña del admin
Resetea desde el shell:
```bash
flask --app run.py shell
>>> from app.models import User
>>> from app import db
>>> admin = User.query.filter_by(email='admin@condoadmin.com').first()
>>> admin.set_password('nueva_password')
>>> db.session.commit()
```

### La página se ve sin estilos
Tailwind CSS se carga desde CDN. Verifica tu conexión a internet.

## 📱 Usar en Producción

### 1. Cambiar Configuración
```bash
# En .env
FLASK_ENV=production
SECRET_KEY=genera-una-clave-muy-segura-aqui
```

### 2. Usar Base de Datos Real
```bash
# PostgreSQL
DATABASE_URL=postgresql://usuario:password@localhost/condoadmin

# MySQL
DATABASE_URL=mysql://usuario:password@localhost/condoadmin
```

### 3. Usar Servidor WSGI
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

### 4. Configurar NGINX (Opcional)
```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Siguientes Pasos

1. **Personaliza**: Cambia nombres, colores y logos
2. **Agrega Datos**: Crea usuarios, instalaciones y cuentas reales
3. **Prueba**: Navega por todos los módulos
4. **Extiende**: Agrega nuevas funcionalidades según necesites
5. **Despliega**: Sube a producción con Gunicorn + NGINX

## 💡 Tips Pro

- Usa el comando `flask shell` para operaciones por lotes
- Los permisos se pueden cambiar sin reiniciar la app
- Haz backup regular de `condo_admin.db`
- Revisa los logs para debuggear problemas
- Las migraciones se manejan automáticamente

## 🎓 Recursos de Aprendizaje

- **Flask**: https://flask.palletsprojects.com/
- **SQLAlchemy**: https://www.sqlalchemy.org/
- **Tailwind CSS**: https://tailwindcss.com/
- **Font Awesome**: https://fontawesome.com/

---

¿Necesitas ayuda? Revisa el README.md completo o abre un issue. 🚀
