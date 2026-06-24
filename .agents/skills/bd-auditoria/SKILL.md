---
name: bd-auditoria
description: Administrar, auditar, monitorear y conectar eventos de bases de datos. Usar para gestionar accesos SaaS, perfiles de conexión a PostgreSQL, MySQL, SQLite y MongoDB, inyectar triggers de auditoría, monitorear operaciones DML en tiempo real, cargar reportes CSV y visualizar métricas en el panel de administrador.
---

# Sistema de Auditoría de Bases de Datos

Utilizar este sistema como una plataforma centralizada para administrar y auditar eventos de bases de datos de diferentes clientes. Construido con Python y Streamlit, permite capturar operaciones de cambio (Insert, Update, Delete) en tiempo real.

## Flujo de Trabajo y Módulos

1. **Acceso y Registro (`app.py`)**
   Gestionar el acceso seguro (SaaS) mediante registro de usuarios, roles (Admin y Cliente) e inicios de sesión. La información se almacena en una base de datos local SQLite (`saas_admin.db`).

2. **Gestor de Conexión (`pages/3_Conectar_BD.py`)**
   Conectar a bases de datos de clientes (PostgreSQL, MySQL, SQLite y MongoDB). Permitir guardar perfiles de conexión y automatizar la instalación del núcleo de auditoría, inyectando triggers SQL o listeners de Change Stream.

3. **Monitoreo en Vivo (`pages/1_Monitoreo_Vivo.py`)**
   Realizar seguimiento en tiempo real de operaciones y transacciones. Filtrar y visualizar logs con auto-refresco y generar scripts de reversión (rollback).

4. **Cargador de CSV (`pages/2_Cargador_CSV.py`)**
   Importar y analizar reportes de auditoría históricos en formato CSV. Facilitar búsquedas rápidas utilizando la librería Pandas.

5. **Panel de Admin (`pages/4_Panel_Admin.py`)**
   Exponer estadísticas globales, métricas de inicio de sesión, listado de usuarios y uso de motores de bases de datos mediante un dashboard administrativo.

## Integraciones y Dependencias

- **Sistemas Externos**: El sistema está integrado con 2 sistemas adicionales que se manejan independientemente del proyecto original (Validación de sintaxis y Normalización).
- **Tecnologías**: Las dependencias se encuentran en `requirements.txt`.
  - Lenguaje: Python 3.10+
  - Web: `streamlit` y `streamlit-autorefresh`
  - Datos: `pandas`
  - Controladores: `psycopg2-binary` (PostgreSQL), `pymysql` (MySQL), `pymongo` (MongoDB), y el módulo integrado `sqlite3`.
