-- ==========================================
-- 0. LIMPIEZA PREVIA (Para evitar choques al re-ejecutar)
-- ==========================================
RESET ROLE;
DROP TABLE IF EXISTS public.PRODUCTOS CASCADE;
DROP TABLE IF EXISTS public.VENTAS CASCADE;

-- ==========================================
-- 1. CREAR USUARIOS (ROLES) SIMULADOS
-- (Ignora el error si te dice que ya existen)
-- ==========================================
-- CREATE ROLE admin_inventario;
-- CREATE ROLE app_ventas;
-- *Ya están creados de tu ejecución anterior, así que saltamos este paso*

-- ==========================================
-- 2. CREAR NUEVAS TABLAS
-- ==========================================
CREATE TABLE public.PRODUCTOS (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100),
    precio NUMERIC(10,2),
    stock INT
);

CREATE TABLE public.VENTAS (
    id SERIAL PRIMARY KEY,
    producto_id INT,
    cantidad INT,
    total NUMERIC(10,2)
);

-- ==========================================
-- 3. OTORGAR PERMISOS (¡AQUÍ ESTÁ LA MAGIA CORREGIDA!)
-- ==========================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_inventario, app_ventas;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO admin_inventario, app_ventas;

-- ==========================================
-- 4. ASIGNAR EL TRIGGER DE AUDITORÍA
-- ==========================================
CREATE TRIGGER trg_auditoria_productos
    AFTER INSERT OR UPDATE OR DELETE ON public.PRODUCTOS
    FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_generica();

CREATE TRIGGER trg_auditoria_ventas
    AFTER INSERT OR UPDATE OR DELETE ON public.VENTAS
    FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_generica();

-- ==========================================
-- 5. SIMULAR ACTIVIDAD DEL ADMIN DE INVENTARIO
-- ==========================================
SET ROLE admin_inventario;

INSERT INTO public.PRODUCTOS (nombre, precio, stock) VALUES
('Laptop Pro 15', 1500.00, 50),
('Mouse Inalámbrico', 25.50, 200),
('Teclado Mecánico', 85.00, 100),
('Monitor 27" 4K', 350.00, 30);

UPDATE public.PRODUCTOS SET stock = 45 WHERE nombre = 'Laptop Pro 15';
UPDATE public.PRODUCTOS SET precio = 80.00 WHERE nombre = 'Teclado Mecánico';
DELETE FROM public.PRODUCTOS WHERE nombre = 'Mouse Inalámbrico';

-- ==========================================
-- 6. SIMULAR ACTIVIDAD DEL SISTEMA DE VENTAS
-- ==========================================
SET ROLE app_ventas;

INSERT INTO public.VENTAS (producto_id, cantidad, total) VALUES
(1, 2, 3000.00),
(3, 1, 80.00),
(4, 5, 1750.00);

UPDATE public.VENTAS SET cantidad = 3, total = 4500.00 WHERE id = 1;

-- ==========================================
-- 7. VOLVER AL USUARIO PRINCIPAL Y AJUSTAR FECHAS
-- ==========================================
RESET ROLE;

UPDATE public.AUDITORIA_LOGS
SET fecha_hora = fecha_hora - INTERVAL '2 days'
WHERE tabla_nombre = 'public.productos';

UPDATE public.AUDITORIA_LOGS
SET fecha_hora = fecha_hora - INTERVAL '1 day'
WHERE tabla_nombre = 'public.ventas';