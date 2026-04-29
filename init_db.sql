-- =============================================================================
-- SISTEMA DE AUDITORÍA NO INVASIVO PARA POSTGRESQL
-- DBA Sénior Script | Versión 1.0
-- Compatibilidad: PostgreSQL 12+
-- =============================================================================

-- -----------------------------------------------------------------------------
-- SECCIÓN 1: TABLA DE EJEMPLO — USUARIOS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.USUARIOS (
    id       SERIAL       PRIMARY KEY,
    nombre   VARCHAR(100) NOT NULL,
    email    VARCHAR(150) NOT NULL UNIQUE,
    salario  NUMERIC(12, 2)
);

COMMENT ON TABLE  public.USUARIOS         IS 'Tabla de usuarios del sistema';
COMMENT ON COLUMN public.USUARIOS.id      IS 'Identificador único autoincremental';
COMMENT ON COLUMN public.USUARIOS.nombre  IS 'Nombre completo del usuario';
COMMENT ON COLUMN public.USUARIOS.email   IS 'Correo electrónico único';
COMMENT ON COLUMN public.USUARIOS.salario IS 'Salario mensual en moneda local';


-- -----------------------------------------------------------------------------
-- SECCIÓN 2: TABLA CENTRALIZADA DE LOGS — AUDITORIA_LOGS
-- -----------------------------------------------------------------------------
-- Diseño:
--   • operacion  : I (INSERT) | U (UPDATE) | D (DELETE)
--   • valores_old: snapshot JSONB previo al cambio (NULL en INSERT)
--   • valores_new: snapshot JSONB posterior al cambio (NULL en DELETE)
--   • ip_cliente : dirección IP obtenida con inet_client_addr()
--                  (NULL cuando la sesión es local / socket Unix)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.AUDITORIA_LOGS (
    log_id       BIGSERIAL    PRIMARY KEY,
    tabla_nombre TEXT         NOT NULL,
    operacion    CHAR(1)      NOT NULL CHECK (operacion IN ('I', 'U', 'D')),
    usuario_bd   TEXT         NOT NULL DEFAULT current_user,
    ip_cliente   INET,                          -- NULL si conexión local
    fecha_hora   TIMESTAMPTZ  NOT NULL DEFAULT clock_timestamp(),
    valores_old  JSONB,                         -- NULL en INSERT
    valores_new  JSONB                          -- NULL en DELETE
);

-- Índices de soporte para consultas de trazabilidad frecuentes
CREATE INDEX IF NOT EXISTS idx_audit_tabla
    ON public.AUDITORIA_LOGS (tabla_nombre);

CREATE INDEX IF NOT EXISTS idx_audit_fecha
    ON public.AUDITORIA_LOGS (fecha_hora DESC);

CREATE INDEX IF NOT EXISTS idx_audit_usuario
    ON public.AUDITORIA_LOGS (usuario_bd);

CREATE INDEX IF NOT EXISTS idx_audit_operacion
    ON public.AUDITORIA_LOGS (operacion);

-- Índice GIN para búsqueda eficiente dentro de los valores JSON
CREATE INDEX IF NOT EXISTS idx_audit_valores_new_gin
    ON public.AUDITORIA_LOGS USING GIN (valores_new);

CREATE INDEX IF NOT EXISTS idx_audit_valores_old_gin
    ON public.AUDITORIA_LOGS USING GIN (valores_old);

COMMENT ON TABLE  public.AUDITORIA_LOGS              IS 'Log centralizado de auditoría para todas las tablas instrumentadas';
COMMENT ON COLUMN public.AUDITORIA_LOGS.log_id       IS 'PK autoincremental del registro de auditoría';
COMMENT ON COLUMN public.AUDITORIA_LOGS.tabla_nombre IS 'Nombre de la tabla afectada (esquema.tabla)';
COMMENT ON COLUMN public.AUDITORIA_LOGS.operacion    IS 'Tipo de operación: I=INSERT, U=UPDATE, D=DELETE';
COMMENT ON COLUMN public.AUDITORIA_LOGS.usuario_bd   IS 'Usuario de base de datos que ejecutó la operación';
COMMENT ON COLUMN public.AUDITORIA_LOGS.ip_cliente   IS 'IP del cliente; NULL si conexión por socket Unix';
COMMENT ON COLUMN public.AUDITORIA_LOGS.fecha_hora   IS 'Timestamp con zona horaria del momento exacto del cambio';
COMMENT ON COLUMN public.AUDITORIA_LOGS.valores_old  IS 'Fila completa antes del cambio (JSONB); NULL en INSERT';
COMMENT ON COLUMN public.AUDITORIA_LOGS.valores_new  IS 'Fila completa después del cambio (JSONB); NULL en DELETE';


-- -----------------------------------------------------------------------------
-- SECCIÓN 3: FUNCIÓN DE TRIGGER GENÉRICA Y OPTIMIZADA
-- -----------------------------------------------------------------------------
-- Diseño:
--   • Usa hstore_to_jsonb(hstore(OLD/NEW)) → compatible con cualquier esquema
--   • SECURITY DEFINER para garantizar escritura en AUDITORIA_LOGS sin
--     necesidad de otorgar permisos directos al rol de aplicación
--   • SET search_path = public evita ataques de search_path injection
--   • Retorna NEW en INSERT/UPDATE y OLD en DELETE (buena práctica)
-- -----------------------------------------------------------------------------

-- La extensión hstore es necesaria para la conversión genérica de filas a JSONB
CREATE EXTENSION IF NOT EXISTS hstore;

CREATE OR REPLACE FUNCTION public.fn_auditoria_generica()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER                -- Ejecuta con privilegios del propietario
SET search_path = public        -- Protección contra search_path injection
AS $$
DECLARE
    v_old_data  JSONB := NULL;
    v_new_data  JSONB := NULL;
    v_operacion CHAR(1);
BEGIN
    -- ── Determinar tipo de operación ─────────────────────────────────────────
    IF    TG_OP = 'INSERT' THEN v_operacion := 'I';
    ELSIF TG_OP = 'UPDATE' THEN v_operacion := 'U';
    ELSIF TG_OP = 'DELETE' THEN v_operacion := 'D';
    END IF;

    -- ── Serializar filas OLD / NEW a JSONB ───────────────────────────────────
    -- hstore(OLD) convierte el registro completo en pares clave→valor
    -- sin necesidad de conocer las columnas de antemano (genérico).
    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        v_old_data := hstore_to_jsonb(hstore(OLD));
    END IF;

    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        v_new_data := hstore_to_jsonb(hstore(NEW));
    END IF;

    -- ── Insertar registro de auditoría ───────────────────────────────────────
    INSERT INTO public.AUDITORIA_LOGS (
        tabla_nombre,
        operacion,
        usuario_bd,
        ip_cliente,
        fecha_hora,
        valores_old,
        valores_new
    ) VALUES (
        TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,   -- ej: 'public.usuarios'
        v_operacion,
        current_user,                               -- usuario de BD activo
        inet_client_addr(),                         -- IP; NULL si socket local
        clock_timestamp(),                          -- tiempo real (no transacción)
        v_old_data,
        v_new_data
    );

    -- ── Retornar la fila correcta según el tipo de operación ─────────────────
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;

EXCEPTION
    -- Captura fallos de auditoría sin afectar la transacción principal
    WHEN OTHERS THEN
        RAISE WARNING '[AUDITORIA] Error al registrar log para %.%: % (SQLSTATE: %)',
            TG_TABLE_SCHEMA, TG_TABLE_NAME, SQLERRM, SQLSTATE;
        IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
        RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.fn_auditoria_generica() IS
    'Trigger genérico de auditoría. Captura INSERT/UPDATE/DELETE en AUDITORIA_LOGS '
    'con usuario de BD, IP del cliente y snapshots OLD/NEW en JSONB. '
    'No invasivo: no modifica la tabla observada.';


-- -----------------------------------------------------------------------------
-- SECCIÓN 4: ASIGNACIÓN DEL TRIGGER A LA TABLA USUARIOS
-- -----------------------------------------------------------------------------
-- AFTER: no bloquea la operación; el log se escribe una vez confirmada la fila
-- FOR EACH ROW: se audita cada fila individualmente (necesario para OLD/NEW)
-- -----------------------------------------------------------------------------

DROP TRIGGER IF EXISTS trg_auditoria_usuarios ON public.USUARIOS;

CREATE TRIGGER trg_auditoria_usuarios
    AFTER INSERT OR UPDATE OR DELETE
    ON public.USUARIOS
    FOR EACH ROW
    EXECUTE FUNCTION public.fn_auditoria_generica();

COMMENT ON TRIGGER trg_auditoria_usuarios ON public.USUARIOS IS
    'Trigger AFTER que invoca fn_auditoria_generica() para INSERT, UPDATE y DELETE '
    'en la tabla USUARIOS. Registra trazabilidad completa en AUDITORIA_LOGS.';


-- =============================================================================
-- SECCIÓN 5: DATOS DE PRUEBA Y VERIFICACIÓN
-- =============================================================================

-- Insertar filas de prueba
INSERT INTO public.USUARIOS (nombre, email, salario)
VALUES
    ('Ana Torres',   'ana.torres@empresa.com',   4500.00),
    ('Luis Mamani',  'luis.mamani@empresa.com',  3800.50),
    ('Carla Quispe', 'carla.quispe@empresa.com', 5200.00);

-- Actualizar una fila (generará un log con OLD y NEW)
UPDATE public.USUARIOS
SET salario = 5000.00
WHERE email = 'luis.mamani@empresa.com';

-- Eliminar una fila (generará un log con OLD solamente)
DELETE FROM public.USUARIOS
WHERE email = 'carla.quispe@empresa.com';

-- -----------------------------------------------------------------------------
-- Consulta de verificación del log completo
-- -----------------------------------------------------------------------------
SELECT
    log_id,
    tabla_nombre,
    operacion,
    usuario_bd,
    COALESCE(ip_cliente::TEXT, '(local/socket)') AS ip_cliente,
    fecha_hora,
    valores_old,
    valores_new
FROM public.AUDITORIA_LOGS
ORDER BY log_id;


-- =============================================================================
-- SECCIÓN 6: CONSULTAS DE TRAZABILIDAD ÚTILES
-- =============================================================================

-- ── ¿Quién modificó qué y cuándo? ───────────────────────────────────────────
-- SELECT
--     log_id,
--     operacion,
--     usuario_bd,
--     ip_cliente,
--     fecha_hora,
--     valores_old -> 'salario' AS salario_anterior,
--     valores_new -> 'salario' AS salario_nuevo
-- FROM public.AUDITORIA_LOGS
-- WHERE tabla_nombre = 'public.usuarios'
--   AND operacion = 'U'
-- ORDER BY fecha_hora DESC;

-- ── Historial completo de un registro por su PK ──────────────────────────────
-- SELECT * FROM public.AUDITORIA_LOGS
-- WHERE (valores_old ->> 'id' = '2' OR valores_new ->> 'id' = '2')
-- ORDER BY fecha_hora;

-- ── Actividad por usuario en las últimas 24 h ────────────────────────────────
-- SELECT usuario_bd, COUNT(*) AS total_ops
-- FROM public.AUDITORIA_LOGS
-- WHERE fecha_hora >= NOW() - INTERVAL '24 hours'
-- GROUP BY usuario_bd
-- ORDER BY total_ops DESC;