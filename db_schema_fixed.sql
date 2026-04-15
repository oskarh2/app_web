-- ============================================================================
-- SCRIPT SQL LIMPIO - SIN PROBLEMAS DE ESCHEMA
-- ============================================================================

-- 1. Extensiones necesarias (crear primero)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Función trigger actualizado_at
CREATE OR REPLACE FUNCTION public.set_current_timestamp_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. Tabla empresas
CREATE TABLE public.empresas (
    codigo UUID PRIMARY KEY DEFAULT uuid_generate_v1(),
    nombre VARCHAR(255) NOT NULL,
    nit VARCHAR(50) UNIQUE NOT NULL,
    direccion TEXT,
    pais VARCHAR(100),
    activo BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tabla usuarios
CREATE TABLE public.usuarios (
    perfil_id INTEGER PRIMARY KEY,
    empresa UUID REFERENCES public.empresas(codigo) ON DELETE SET NULL,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'viewer')),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tabla ventas
CREATE TABLE public.ventas (
    id SERIAL PRIMARY KEY,
    empresa UUID NOT NULL REFERENCES public.empresas(codigo) ON DELETE CASCADE,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 0 CHECK (cantidad >= 0),
    monto_total DECIMAL(15, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Tabla reg_consulta
CREATE TABLE public.reg_consulta (
    consulta_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario INTEGER NOT NULL,
    empresa UUID NOT NULL REFERENCES public.empresas(codigo) ON DELETE CASCADE,
    fecha_hora TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    estado VARCHAR(50) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'en_proceso', 'completada', 'cancelada')),
    prioridad INTEGER DEFAULT 5 CHECK (prioridad BETWEEN 1 AND 10),
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Tabla detalle_reg_consulta
CREATE TABLE public.detalle_reg_consulta (
    id SERIAL PRIMARY KEY,
    registro UUID NOT NULL REFERENCES public.reg_consulta(consulta_id) ON DELETE CASCADE,
    pagina INTEGER,
    reg_encontrados INTEGER DEFAULT 0 CHECK (reg_encontrados >= 0),
    tiempo_busqueda_ms INTEGER,
    parametros_busqueda JSONB,
    creado_al TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Tabla archivos
CREATE TABLE public.archivos (
    id SERIAL PRIMARY KEY,
    consulta_id UUID NOT NULL REFERENCES public.reg_consulta(consulta_id) ON DELETE CASCADE,
    archivo_path VARCHAR(500) NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    tamaño_kb BIGINT DEFAULT 0 CHECK (tamaño_kb >= 0),
    subido_por INTEGER REFERENCES public.usuarios(perfil_id) ON DELETE SET NULL,
    hash_md5 CHAR(32),
    contenido_type VARCHAR(100),
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    eliminado BOOLEAN DEFAULT false,
    version INTEGER DEFAULT 1
);

-- 9. Tabla page_tracking (nueva)
CREATE TABLE public.page_tracking (
    page VARCHAR(20) NOT NULL,
    tracking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(5) DEFAULT 'CC',
    kind VARCHAR(2) DEFAULT 'OP',
    steps JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES public.usuarios(perfil_id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}'
);

-- 10. Tabla auditoria
CREATE TABLE public.auditoria (
    id SERIAL PRIMARY KEY,
    tabla VARCHAR(50) NOT NULL,
    accion VARCHAR(20) NOT NULL CHECK (accion IN ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE')),
    id_anterior UUID,
    id_nuevo UUID,
    usuario INTEGER REFERENCES public.usuarios(perfil_id) ON DELETE SET NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_usuario VARCHAR(45),
    datos_anteriores JSONB,
    datos_nuevos JSONB
);

-- 11. Triggers y Vistas (después de crear tablas)
CREATE TRIGGER trg_empresas_set_updated_at
    BEFORE UPDATE ON public.empresas
    FOR EACH ROW EXECUTE FUNCTION public.set_current_timestamp_updated_at();

CREATE VIEW vw_estadisticas_empresas AS
SELECT 
    e.codigo AS empresa_id,
    e.nombre AS empresa_nombre,
    e.nit AS nit,
    COUNT(DISTINCT r.consulta_id) AS total_consultas,
    COUNT(DISTINCT a.id) AS total_archivos,
    SUM(v.cantidad) AS total_ventas,
    SUM(COALESCE(v.monto_total, 0)) AS total_monto_ventas,
    MIN(r.fecha_hora) AS primera_consulta,
    MAX(r.fecha_hora) AS ultima_consulta
FROM public.empresas e
LEFT JOIN public.reg_consulta r ON e.codigo = r.empresa
LEFT JOIN public.archivos a ON e.codigo = a.empresa
LEFT JOIN public.ventas v ON e.codigo = v.empresa
GROUP BY e.codigo, e.nombre, e.nit;

-- Fin del script



