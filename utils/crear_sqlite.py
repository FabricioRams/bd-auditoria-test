import sqlite3

# 1. Esto crea el archivo automáticamente si no existe
conn = sqlite3.connect('cliente_prueba2.db')
cursor = conn.cursor()

# 2. Creamos unas tablas de prueba
cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        suscripcion TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS pagos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monto REAL,
        estado TEXT
    )
''')

# 3. INSERTAR DATOS
# Insertar en tabla 'clientes'
cursor.execute("INSERT INTO clientes (nombre, suscripcion) VALUES ('Juan Pérez', 'Premium')")
cursor.execute("INSERT INTO clientes (nombre, suscripcion) VALUES ('María Gómez', 'Básica')")

# Insertar en tabla 'pagos'
cursor.execute("INSERT INTO pagos (monto, estado) VALUES (150.50, 'Pagado')")
cursor.execute("INSERT INTO pagos (monto, estado) VALUES (50.00, 'Pendiente')")

# IMPORTANTE: Guardar los cambios (commit)
conn.commit()

print("✅ Datos insertados con éxito.")

# --- Opcional: Verificar los datos insertados ---
print("\n--- Clientes ---")
for row in cursor.execute('SELECT * FROM clientes'):
    print(row)

print("\n--- Pagos ---")
for row in cursor.execute('SELECT * FROM pagos'):
    print(row)
# ------------------------------------------------

conn.close()
