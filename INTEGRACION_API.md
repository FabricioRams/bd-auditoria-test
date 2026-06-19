# Guía de Integración: API de Normalización (DataQuest)

¡Hola equipo! 🚀 Hemos habilitado un endpoint público para que puedan consumir nuestro motor heurístico de diagnóstico de normalización (1FN, 2FN, 3FN) directamente desde su código.

No necesitan lidiar con la validación compleja, solo envíennos el esquema SQL de su base de datos y nosotros les responderemos con un diagnóstico estructurado.

## 📡 Enlaces del Servicio

Tenemos dos plataformas corriendo en paralelo:
1. **Interfaz Web (Para humanos):** `https://app-dataquest-web.azurewebsites.net`
2. **Endpoint API (Para consumo de código):** `https://app-dataquest-web-api.azurewebsites.net/api/normalizacion`

Para esta integración, ustedes deberán enviarle sus peticiones HTTP al **Endpoint API**.

**Método:** `POST`
**URL:** `https://app-dataquest-web-api.azurewebsites.net/api/normalizacion`
**CORS:** Habilitado para todos los orígenes (`*`). Pueden llamarlo directo desde el frontend (React, Angular, Vue) sin problemas.

---

## 📥 Qué deben enviarnos (Request)

Deben enviarnos un JSON simple con un campo `sql` que contenga las sentencias `CREATE TABLE` de su base de datos.

**Headers requeridos:**
- `Content-Type: application/json`

**Body (JSON):**
```json
{
  "sql": "CREATE TABLE clientes ( id INT PRIMARY KEY, nombre VARCHAR(100), ciudad VARCHAR(50), region VARCHAR(50) );"
}
```

---

## 📤 Qué les responderemos (Response)

Nuestro servicio parseará su SQL, correrá los algoritmos heurísticos y les devolverá un reporte completo.

### ✅ Caso de Éxito (Status 200 OK)

Recibirán siempre un JSON estructurado así (incluso si la BD está mal diseñada, les diremos por qué en las listas de violaciones):

```json
{
  "success": true,
  "nivel_actual": "2FN",
  "violaciones_1fn": [],
  "violaciones_2fn": [],
  "violaciones_3fn": [
    {
      "tabla": "clientes",
      "determinante": "ciudad",
      "dependientes": ["region"],
      "mensaje": "Dependencia transitiva detectada. Atributos que dependen de 'ciudad' en lugar de la PK."
    }
  ],
  "mejoras_opcionales": [
    {
      "tabla": "clientes",
      "columna": "nombre",
      "tipo": "División Semántica",
      "mensaje": "El atributo 'nombre' puede dividirse para mayor flexibilidad.",
      "sugerencia_columnas": ["nombre", "apellido_paterno", "apellido_materno"]
    }
  ],
  "resumen": "El esquema global se encuentra en nivel: 2FN"
}
```

### ❌ Casos de Error (Status 400 / 500)

Si envían un SQL inválido o el JSON está mal armado:

```json
{
  "success": false,
  "error": {
    "message": "No se encontraron tablas válidas. Revisa la sintaxis de tu CREATE TABLE.",
    "code": 400
  }
}
```

---

## 🧑‍💻 Ejemplo Rápido de Uso (JavaScript / Fetch)

Copien y peguen esto en su frontend o backend para hacer la prueba:

```javascript
const sqlDePrueba = `
  CREATE TABLE empleados (
    emp_id INT PRIMARY KEY, 
    depto_id INT, 
    depto_nombre VARCHAR(100)
  );
`;

async function validarBaseDeDatos() {
  try {
    const response = await fetch("https://app-dataquest-web-api.azurewebsites.net/api/normalizacion", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ sql: sqlDePrueba })
    });

    const data = await response.json();
    
    if (data.success) {
      console.log("¡Diagnóstico Exitoso!");
      console.log("Tu base de datos está en:", data.nivel_actual);
      
      if (data.violaciones_3fn.length > 0) {
        console.warn("Cuidado, detectamos esto en 3FN:", data.violaciones_3fn);
      }
    } else {
      console.error("Error del validador:", data.error.message);
    }
    
  } catch (err) {
    console.error("Error de red intentando contactar la API:", err);
  }
}

validarBaseDeDatos();
```

¡Cualquier duda sobre el formato del SQL o si la API les devuelve algún comportamiento extraño, nos avisan!
