# 🎓 TutorIA — Plataforma de Tutorías Académicas
**Instituto Tecnológico de Matehuala · Ingeniería en Sistemas Computacionales**

Proyecto desarrollado con **Python + Streamlit + Supabase**.

---

## 📁 Estructura del proyecto

```
tutoria_app/
│
├── app.py                     ← Punto de entrada (login / registro)
├── requirements.txt           ← Dependencias Python
├── database_schema.sql        ← Schema completo para Supabase
│
├── pages/
│   ├── alumno.py              ← Dashboard del Alumno
│   ├── docente.py             ← Dashboard del Docente Tutor
│   └── admin.py               ← Panel del Administrador
│
├── components/
│   └── sidebar.py             ← Barra lateral compartida
│
└── utils/
    ├── supabase_client.py     ← Cliente Supabase (cacheado)
    ├── auth.py                ← Login, registro, sesión
    ├── db.py                  ← Operaciones CRUD
    └── styles.py              ← CSS global + helpers de badges
```

---

## 🗄️ Paso 1 — Configurar Supabase

1. Entra a [https://supabase.com](https://supabase.com) y crea un proyecto nuevo.
2. Ve a **SQL Editor** y ejecuta todo el contenido de `database_schema.sql`.
3. En **Authentication → Settings**, activa **Email confirmations** (o desactívalo para desarrollo).
4. Copia tu **Project URL** y tu **anon public key** desde **Settings → API**.

---

## 🚀 Paso 2 — Desplegar en Streamlit Cloud

1. Sube el proyecto a un repositorio de GitHub.
2. Ve a [https://share.streamlit.io](https://share.streamlit.io) y crea una nueva app apuntando a `app.py`.
3. En el panel de la app, abre **Settings → Secrets** y agrega:

```toml
SUPABASE_URL = "https://xxxxxxxxxxxx.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

4. Guarda y despliega. ¡Listo!

---

## 🔒 Roles y permisos

| Rol            | Capacidades |
|----------------|-------------|
| **Alumno**     | Ver disponibilidad, agendar / cancelar sesiones, ver historial |
| **Docente**    | Gestionar disponibilidad, ver sesiones programadas, registrar asistencia y notas |
| **Administrador** | Ver todo, gestionar usuarios, reportes con gráficas y exportación CSV |

> El primer usuario administrador debe crearse directamente desde el panel de Supabase:  
> `Authentication → Users → Invite user`, luego actualizar su `rol` a `administrador`  
> en `Table Editor → perfiles`.

---

## 🔑 Crear usuario administrador manualmente

```sql
-- En el SQL Editor de Supabase, tras registrar el usuario:
UPDATE public.perfiles
SET rol = 'administrador', departamento = 'Coordinación Académica'
WHERE correo = 'admin@instituto.edu.mx';
```

---

## 📦 Dependencias

```
streamlit==1.35.0
supabase==2.5.0
pandas==2.2.2
plotly==5.22.0
python-dateutil==2.9.0
```

---

## 🧑‍💻 Equipo de desarrollo

| Alumno | No. Control |
|--------|-------------|
| Alejandro Morales Peña | 23660408 |
| Ivan Alvarado | 23660149 |
| Pedro Espitia Samaniego | 23660154 |
| Francisco Bernardo Rodríguez Alvarado | 23660167 |

**Materia:** Ingeniería de Software  
**Profesor:** Juan José Robles Conde  
**Semestre:** Sexto · Grupo 6SA
