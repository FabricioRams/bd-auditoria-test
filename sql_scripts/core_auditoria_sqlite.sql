-- =============================================================================
-- SISTEMA DE AUDITORÍA NO INVASIVO PARA SQLITE (NÚCLEO)
-- =============================================================================

CREATE TABLE IF NOT EXISTS AUDITORIA_LOGS (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tabla_nombre TEXT NOT NULL,
    operacion CHAR(1) NOT NULL,
    usuario_bd TEXT,
    ip_cliente TEXT,
    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    valores_old TEXT,
    valores_new TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_tabla ON AUDITORIA_LOGS (tabla_nombre);
CREATE INDEX IF NOT EXISTS idx_audit_fecha ON AUDITORIA_LOGS (fecha_hora DESC);
CREATE INDEX IF NOT EXISTS idx_audit_operacion ON AUDITORIA_LOGS (operacion);
