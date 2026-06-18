import sqlite3
import psycopg2

# Neon.tech credentials
PGHOST='ep-wild-glade-aih26ibl-pooler.c-4.us-east-1.aws.neon.tech'
PGDATABASE='neondb'
PGUSER='neondb_owner'
PGPASSWORD='npg_dV8U1BNZfbus'

print("Iniciando migración...")

try:
    # Conexión a SQLite
    sqlite_conn = sqlite3.connect('saas_admin.db')
    sqlite_cursor = sqlite_conn.cursor()

    # Conexión a PostgreSQL (Neon)
    pg_conn = psycopg2.connect(
        host=PGHOST,
        database=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD,
        sslmode='require'
    )
    pg_cursor = pg_conn.cursor()

    # 1. Crear tablas en PostgreSQL si no existen
    pg_cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol VARCHAR(50) NOT NULL
        )
    ''')

    pg_cursor.execute('''
        CREATE TABLE IF NOT EXISTS registro_accesos (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    pg_cursor.execute('''
        CREATE TABLE IF NOT EXISTS conexiones_guardadas (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            alias VARCHAR(255) NOT NULL,
            motor VARCHAR(50) NOT NULL,
            creds_json TEXT NOT NULL
        )
    ''')
    pg_conn.commit()
    print("Tablas creadas en PostgreSQL.")

    # 2. Migrar la tabla `usuarios`
    sqlite_cursor.execute("SELECT id, username, password, rol FROM usuarios")
    usuarios = sqlite_cursor.fetchall()
    print(f"Migrando {len(usuarios)} usuarios...")
    for user in usuarios:
        try:
            # Upsert para usuarios
            pg_cursor.execute(
                "INSERT INTO usuarios (id, username, password, rol) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
                (user[0], user[1], user[2], user[3])
            )
        except Exception as e:
            print(f"Error migrando usuario {user[1]}: {e}")
            pg_conn.rollback()
    
    # Asegurar que el id de PostgreSQL esté sincronizado con el último insertado
    if usuarios:
        pg_cursor.execute("SELECT setval(pg_get_serial_sequence('usuarios', 'id'), COALESCE((SELECT MAX(id)+1 FROM usuarios), 1), false)")

    # 3. Migrar la tabla `registro_accesos`
    sqlite_cursor.execute("SELECT id, username, fecha_hora FROM registro_accesos")
    accesos = sqlite_cursor.fetchall()
    print(f"Migrando {len(accesos)} registros de accesos...")
    
    # Limpiar tabla en PG antes de migrar si se quiere mantener limpio (opcional, mejor solo insertar)
    # Aquí insertamos todos asumiendo que es una migración única
    for acceso in accesos:
        # Check if already exists just in case (optional, we'll just insert since it's a log)
        pg_cursor.execute(
            "INSERT INTO registro_accesos (id, username, fecha_hora) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
            (acceso[0], acceso[1], acceso[2])
        )
    if accesos:
        pg_cursor.execute("SELECT setval(pg_get_serial_sequence('registro_accesos', 'id'), COALESCE((SELECT MAX(id)+1 FROM registro_accesos), 1), false)")

    # 4. Migrar la tabla `conexiones_guardadas`
    sqlite_cursor.execute("SELECT id, username, alias, motor, creds_json FROM conexiones_guardadas")
    conexiones = sqlite_cursor.fetchall()
    print(f"Migrando {len(conexiones)} conexiones guardadas...")
    for conn_row in conexiones:
        pg_cursor.execute(
            "INSERT INTO conexiones_guardadas (id, username, alias, motor, creds_json) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
            (conn_row[0], conn_row[1], conn_row[2], conn_row[3], conn_row[4])
        )
    if conexiones:
        pg_cursor.execute("SELECT setval(pg_get_serial_sequence('conexiones_guardadas', 'id'), COALESCE((SELECT MAX(id)+1 FROM conexiones_guardadas), 1), false)")

    pg_conn.commit()
    print("Migración completada exitosamente.")

except Exception as e:
    print(f"Ocurrió un error: {e}")

finally:
    if 'sqlite_conn' in locals():
        sqlite_conn.close()
    if 'pg_conn' in locals():
        pg_cursor.close()
        pg_conn.close()
