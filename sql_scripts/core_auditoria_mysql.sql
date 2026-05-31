-- =============================================================================
-- SISTEMA DE AUDITORÍA NO INVASIVO PARA MYSQL (NÚCLEO)
-- =============================================================================

CREATE TABLE IF NOT EXISTS AUDITORIA_LOGS (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tabla_nombre VARCHAR(255) NOT NULL,
    operacion CHAR(1) NOT NULL,
    usuario_bd VARCHAR(255),
    ip_cliente VARCHAR(45),
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valores_old JSON,
    valores_new JSON
);

CREATE INDEX idx_audit_tabla ON AUDITORIA_LOGS (tabla_nombre);
CREATE INDEX idx_audit_fecha ON AUDITORIA_LOGS (fecha_hora DESC);
CREATE INDEX idx_audit_operacion ON AUDITORIA_LOGS (operacion);
