# API de Validación SQL/NoSQL

Servicio para validar la sintaxis de consultas **SQL** y **MongoDB (NoSQL)**.

## Endpoint

```
POST https://validador-per-production.up.railway.app/api/validar
Content-Type: application/json
```

CORS habilitado para cualquier origen (`Access-Control-Allow-Origin: *`).

## Request

| Campo  | Tipo   | Requerido | Descripción |
|--------|--------|-----------|-------------|
| `query` | string | Sí | La consulta SQL o NoSQL a validar. |
| `tipo`  | string | No | `"sql"` o `"nosql"`. Si se omite, se detecta automáticamente. |

```json
{
  "query": "SELECT * FROM usuarios WHERE id = 1;"
}
```

## Responses

### ✅ Consulta válida (200 OK)

```json
{
  "success": true,
  "valid": true,
  "dialect": "SQL Estándar ANSI",
  "confidence": 100,
  "compatible": ["MySQL", "PostgreSQL", "SQLite", "SQL Server", "Oracle"],
  "incompatible": [],
  "errors": [],
  "suggestions": [
    "✅ Sintaxis SQL Estándar ANSI.\nCompatible con:\n✓ MySQL\n✓ PostgreSQL\n✓ SQLite\n✓ SQL Server\n✓ Oracle"
  ]
}
```

### ⚠️ Error de sintaxis (200 OK, `valid: false`)

La petición fue procesada correctamente, pero la consulta tiene errores.

```json
{
  "success": true,
  "valid": false,
  "dialect": "SQL Estándar ANSI",
  "confidence": 100,
  "compatible": ["MySQL", "PostgreSQL", "SQLite", "SQL Server", "Oracle"],
  "incompatible": [],
  "errors": [
    {
      "engine": "SQL Estándar ANSI",
      "line": 1,
      "column": 15,
      "message": "Error sintáctico.\nEncontrado: FORM\nSe esperaba: FROM",
      "fragment": "FORM",
      "suggestion": "Quizás quiso escribir FROM"
    }
  ],
  "suggestions": ["Quizás quiso escribir FROM"]
}
```

Ejemplo para NoSQL (`db.usuarios.selectData({...})`):

```json
{
  "success": true,
  "valid": false,
  "dialect": "MongoDB",
  "confidence": 100,
  "errors": [
    {
      "line": 1,
      "column": 13,
      "message": "Comando desconocido \"selectData\".",
      "operator": null,
      "fragment": "selectData",
      "suggestion": "Soportados: find, findOne, insertOne, insertMany, updateOne, updateMany, replaceOne, deleteOne, deleteMany, aggregate..."
    }
  ],
  "suggestions": ["Soportados: find, findOne, insertOne, insertMany, updateOne, updateMany, replaceOne, deleteOne, deleteMany, aggregate..."]
}
```

### ❌ Errores

**400 — Request inválida** (falta `query`, está vacío, o `tipo` no es válido):

```json
{
  "success": false,
  "error": {
    "message": "El campo 'query' es requerido y debe ser un string no vacío.",
    "code": 400
  }
}
```

**500 — Error interno del servidor:**

```json
{
  "success": false,
  "error": {
    "message": "Error interno del servidor al procesar la consulta.",
    "code": 500
  }
}
```

## Códigos de estado

| Código | Significado |
|--------|-------------|
| 200 | Petición procesada (revisar `valid` para saber si la consulta es correcta). |
| 400 | Body inválido (`query` faltante/vacío o `tipo` desconocido). |
| 500 | Error inesperado del servidor. |

## Ejemplo de consumo (JavaScript / TypeScript)

```ts
async function validarConsulta(query: string, tipo?: 'sql' | 'nosql') {
  const res = await fetch('https://validador-per-production.up.railway.app/api/validar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, tipo })
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error?.message ?? `Error HTTP ${res.status}`);
  }

  return data; // { success, valid, dialect, errors, suggestions, ... }
}

// Uso
const resultado = await validarConsulta('SELECT * FROM usuarios WHERE id = 1;');
if (resultado.valid) {
  console.log('Consulta válida:', resultado.dialect);
} else {
  console.log('Errores:', resultado.errors);
}
```
