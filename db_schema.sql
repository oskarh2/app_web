-- ============================================================================
-- DB Schema: GestorConsultas - PostgreSQL v15+
-- Autor: System Generated
-- Fecha: $(date +%Y-%m-%d)
-- ============================================================================

-- Configuración de sesión
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = 'content';
SET client_min_messages = warning;
SET row_security = off;

-- Funciones y extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- Para análisis de rendimiento
COMMENT ON EXTENSION "pgcrypto" IS 'funciones criptográficas';

-- ============================================================================
-- FUNCIONES UTILITARIAS
-- ============================================================================

CREATE OR REPLACE FUNCTION public.set_current_timestamp_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.set_current_timestamp_updated_at() IS 'Triggers que actualiza updated_at automáticamente';

CREATE OR REPLACE FUNCTION public.generate_unique_query_id()
RETURNS UUID AS $$
BEGIN
    RETURN gen_random_uuid();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.generate_unique_query_id() IS 'Genera IDs únicos para consultas';

-- ============================================================================
-- TABLA DE EMPRESAS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.empresas (
    codigo UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    nit VARCHAR(50) UNIQUE NOT NULL,
    direccion TEXT,
    pais VARCHAR(100),
    activo BOOLEAN DEFAULT true,
    metadata JSONB, -- Campo nativo de PostgreSQL para datos estructurados
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices principales para empresas
CREATE INDEX idx_empresas_nombre ON public.empresas(nombre);
CREATE INDEX idx_empresas_nit ON public.empresas(nit);
CREATE INDEX idx_empresas_activo ON public.empresas(activo) WHERE activo = true;
CREATE INDEX idx_empresas_created_at ON public.empresas(created_at DESC);
CREATE UNIQUE INDEX uq_empresas_nit ON public.empresas(lower(nit));

-- Comentarios sobre la tabla
COMMENT ON TABLE public.empresas IS 'Registro de empresas clientes o asociadas al sistema';
COMMENT ON COLUMN public.empresas.metadata IS 'Almacena metadatos adicionales en formato JSONB para flexibilidad';

-- Trigger para actualizar updated_at automáticamente
CREATE TRIGGER trg_empresas_set_updated_at
    BEFORE UPDATE ON public.empresas
    FOR EACH ROW EXECUTE FUNCTION public.set_current_timestamp_updated_at();

-- ============================================================================
-- TABLA DE USUARIOS (EXTENSIÓN DE AUTH_USER)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.usuarios (
    perfil_id INTEGER PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    empresa UUID REFERENCES public.empresas(codigo) ON DELETE SET NULL,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'viewer')),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuarios_perfil FOREIGN KEY (perfil_id) REFERENCES auth.users(id)
);

-- Índices principales para usuarios
CREATE INDEX idx_usuarios_empresa ON public.usuarios(empresa);
CREATE INDEX idx_usuarios_role ON public.usuarios(role);
CREATE INDEX idx_usuarios_fecha_registro ON public.usuarios(fecha_registro DESC);
CREATE UNIQUE INDEX uq_usuarios_perfil_id ON public.usuarios(perfil_id);

-- Comentarios sobre la tabla
COMMENT ON TABLE public.usuarios IS 'Extensión de usuario de Django con roles y vinculación a empresa';
COMMENT ON COLUMN public.usuarios.perfil_id IS 'FK a auth.users - ID del usuario autenticado';

-- ============================================================================
-- TABLA DE VENTAS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.ventas (
    id SERIAL PRIMARY KEY,
    empresa UUID NOT NULL REFERENCES public.empresas(codigo) ON DELETE CASCADE,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 0 CHECK (cantidad >= 0),
    monto_total DECIMAL(15, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_fechas_ventas CHECK (fecha_inicio <= fecha_fin)
);

-- Índices principales para ventas
CREATE INDEX idx_ventas_empresa ON public.ventas(empresa);
CREATE INDEX idx_ventas_fecha_inicio ON public.ventas(fecha_inicio);
CREATE INDEX idx_ventas_fecha_fin ON public.ventas(fecha_fin);
CREATE INDEX idx_ventas_rango ON public.ventas(fecha_inicio, fecha_fin);
CREATE INDEX idx_ventas_monto ON public.ventas(monto_total);

-- Comentarios sobre la tabla
COMMENT ON TABLE public.ventas IS 'Registro histórico de transacciones de ventas por periodo';
COMMENT ON COLUMN public.ventas.monto_total IS 'Valor monetario total de la venta en periodo';

-- Trigger para actualizar updated_at automáticamente
CREATE TRIGGER trg_ventas_set_updated_at
    BEFORE UPDATE ON public.ventas
    FOR EACH ROW EXECUTE FUNCTION public.set_current_timestamp_updated_at();

-- ============================================================================
-- TABLA DE CONSULTAS (REG_CONSULTA)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.reg_consulta (
    consulta_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario INTEGER NOT NULL REFERENCES public.usuarios(perfil_id) ON DELETE CASCADE,
    empresa UUID NOT NULL REFERENCES public.empresas(codigo) ON DELETE CASCADE,
    fecha_hora TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    estado VARCHAR(50) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'en_proceso', 'completada', 'cancelada')),
    prioridad INTEGER DEFAULT 5 CHECK (prioridad BETWEEN 1 AND 10), -- 1=Alta, 10=Baja
    creador_ip VARCHAR(45), -- IP del cliente para auditoría
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices principales para consultas
CREATE INDEX idx_reg_consulta_usuario ON public.reg_consulta(usuario);
CREATE INDEX idx_reg_consulta_empresa ON public.reg_consulta(empresa);
CREATE INDEX idx_reg_consulta_fecha_hora ON public.reg_consulta(fecha_hora DESC);
CREATE INDEX idx_reg_consulta_estado ON public.reg_consulta(estado);
CREATE INDEX idx_reg_consulta_composite ON public.reg_consulta(usuario, empresa, fecha_hora DESC);
CREATE INDEX idx_reg_consulta_prioridad ON public.reg_consulta(prioridad ASC) WHERE prioridad <= 3;

-- Comentarios sobre la tabla
COMMENT ON TABLE public.reg_consulta IS 'Tabla principal de registro de consultas generadas por usuarios';
COMMENT ON COLUMN public.reg_consulta.consulta_id IS 'ID único generado automáticamente para cada consulta';
COMMENT ON COLUMN public.reg_consulta.prioridad IS 'Nivel de prioridad: 1 es más urgente que 10';

-- ============================================================================
-- TABLA DETALLE DE CONSULTA (DETALLE_REG_CONSULTA)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.detalle_reg_consulta (
    id SERIAL PRIMARY KEY,
    registro UUID NOT NULL REFERENCES public.reg_consulta(consulta_id) ON DELETE CASCADE,
    pagina INTEGER,
    reg_encontrados INTEGER DEFAULT 0 CHECK (reg_encontrados >= 0),
    tiempo_busqueda_ms INTEGER,
    parametros_busqueda JSONB, -- Almacenar parámetros complejos en JSONB
    creado_al TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices principales para detalles
CREATE INDEX idx_detalle_registro ON public.detalle_reg_consulta(registro);
CREATE INDEX idx_detalle_pagina ON public.detalle_reg_consulta(pagina) WHERE pagina IS NOT NULL;
CREATE INDEX idx_detalle_tiempos ON public.detalle_reg_consulta(tiempo_busqueda_ms);
CREATE INDEX idx_detalle_search ON public.detalle_reg_consulta(pagina, reg_encontrados DESC);

-- Comentarios sobre la tabla
COMMENT ON TABLE public.detalle_reg_consulta IS 'Detalles técnicos de cada resultado de consulta';
COMMENT ON COLUMN public.detalle_reg_consulta.parametros_busqueda IS 'Guarda los filtros/criterios aplicados en la búsqueda';

-- ============================================================================
-- NUEVA TABLA: PAGE_TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.page_tracking (
    page VARCHAR(20) NOT NULL,
    tracking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(5) DEFAULT 'CC',  -- CC = Continuous Cycle, OTRA APLICAR VALIDACIÓN
    kind VARCHAR(2) DEFAULT 'OP',  -- OP = Operation, EJECUCION, etc.
    steps JSONB,  -- Guardar estado de pasos como estructura JSONB de PostgreSQL
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES public.usuarios(perfil_id) ON DELETE SET NULL,
    metadata JSONB  -- Datos adicionales flexibles
    
);

-- Índices principales para rendimiento
CREATE INDEX idx_page_tracking_page ON public.page_tracking(page);
CREATE INDEX idx_page_tracking_status ON public.page_tracking(status);
CREATE INDEX idx_page_tracking_type ON public.page_tracking(type);
CREATE INDEX idx_page_tracking_user ON public.page_tracking(user_id);
CREATE INDEX idx_page_tracking_created_at ON public.page_tracking(created_at DESC);
CREATE INDEX idx_page_tracking_kind ON public.page_tracking(kind);

-- Trigger para actualizar updated_at automáticamente
CREATE TRIGGER trg_page_tracking_set_updated_at
    BEFORE UPDATE ON public.page_tracking
    FOR EACH ROW EXECUTE FUNCTION public.set_current_timestamp_updated_at();

COMMENT ON TABLE public.page_tracking IS 'Tabla de rastreo de páginas y flujos de trabajo';
COMMENT ON COLUMN public.page_tracking.tracking_id IS 'ID único generado automáticamente para cada registro';
COMMENT ON COLUMN public.page_tracking.steps IS 'Estado actual de los pasos en formato JSONB';
COMMENT ON COLUMN public.page_tracking.status IS 'Estado de la ejecución: PENDING, IN_PROGRESS, COMPLETED, FAILED';


-- ============================================================================
-- TABLA DE ARCHIVOS CARGADOS (ARCHIVOS)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.archivos (
    id SERIAL PRIMARY KEY,
    consulta_id UUID NOT NULL REFERENCES public.reg_consulta(consulta_id) ON DELETE CASCADE,
    archivo_path VARCHAR(500) NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    tamaño_kb BIGINT DEFAULT 0 CHECK (tamaño_kb >= 0),
    subido_por INTEGER REFERENCES public.usuarios(perfil_id) ON DELETE SET NULL,
    hash_md5 CHAR(32), -- Hash para verificar integridad
    contenido_type VARCHAR(100),
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    eliminado BOOLEAN DEFAULT false,
    version INTEGER DEFAULT 1
);

-- Índices principales para archivos
CREATE INDEX idx_archivos_consulta ON public.archivos(consulta_id);
CREATE INDEX idx_archivos_subido_por ON public.archivos(subido_por);
CREATE INDEX idx_archivos_creado_en ON public.archivos(creado_en DESC);
CREATE INDEX idx_archivos_hash ON public.archivos(hash_md5);
CREATE INDEX idx_archivos_extension ON public.archivos(nombre_archino) WHERE nombre_archivo LIKE '%.pdf' OR nombre_archivo LIKE '%.csv' OR nombre_archivo LIKE '%.xlsx';

-- Comentarios sobre la tabla
COMMENT ON TABLE public.archivos IS 'Repositorio de archivos vinculados a consultas específicas';
COMMENT ON COLUMN public.archivos.hash_md5 IS 'Hash criptográfico para verificar que el archivo no fue modificado';
COMMENT ON COLUMN public.archivos.version IS 'Número de versión del archivo (útil para actualizaciones)';

-- ============================================================================
-- TABLA DE AUDITORÍA (TRIGGERS Y LOGGING)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.auditoria (
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

-- Índice para auditoría rápida
CREATE INDEX idx_auditoria_tabla ON public.auditoria(tabla);
CREATE INDEX idx_auditoria_usuario ON public.auditoria(usuario);
CREATE INDEX idx_auditoria_timestamp ON public.auditoria(timestamp DESC);

COMMENT ON TABLE public.auditoria IS 'Bitácora de cambios realizados en las tablas principales';

-- ============================================================================
-- TRIGGERS DE AUDITORÍA AUTOMÁTICA
-- ============================================================================

CREATE OR REPLACE FUNCTION public.log_changes_to_audit()
RETURNS TRIGGER AS $$
DECLARE
    json_data_old JSONB;
    json_data_new JSONB;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        json_data_old := to_jsonb(OLD);
        json_data_new := to_jsonb(NEW);
        
        INSERT INTO public.auditoria(
            tabla, accion, id_anterior, id_nuevo, usuario, 
            datos_anteriores, datos_nuevos
        ) VALUES (
            TG_TABLE_NAME, 'UPDATE', OLD.id::UUID, NEW.id::UUID, 
            COALESCE((SELECT perfil_id FROM public.usuarios WHERE perfil_id = auth.uid()), NULL::INTEGER),
            json_data_old, json_data_new
        );
    ELSIF TG_OP = 'DELETE' THEN
        json_data_old := to_jsonb(OLD);
        
        INSERT INTO public.auditoria(
            tabla, accion, id_anterior, datos_anteriores
        ) VALUES (
            TG_TABLE_NAME, 'DELETE', OLD.id::UUID, json_data_old
        );
    ELSIF TG_OP = 'INSERT' THEN
        json_data_new := to_jsonb(NEW);
        
        INSERT INTO public.auditoria(
            tabla, accion, id_nuevo, datos_nuevos
        ) VALUES (
            TG_TABLE_NAME, 'INSERT', NEW.id::UUID, json_data_new
        );
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Activar triggers de auditoría para todas las tablas
CREATE TRIGGER trg_log_empresas
    AFTER INSERT OR UPDATE OR DELETE ON public.empresas
    FOR EACH ROW EXECUTE FUNCTION public.log_changes_to_audit();

CREATE TRIGGER trg_log_ventas
    AFTER INSERT OR UPDATE OR DELETE ON public.ventas
    FOR EACH ROW EXECUTE FUNCTION public.log_changes_to_audit();

CREATE TRIGGER trg_log_reg_consulta
    AFTER INSERT OR UPDATE OR DELETE ON public.reg_consulta
    FOR EACH ROW EXECUTE FUNCTION public.log_changes_to_audit();

-- ============================================================================
-- FUNCIONALIDAD DE SEGURIDAD
-- ============================================================================

-- Restricciones de integridad referencial
ALTER TABLE public.usuarios ADD CONSTRAINT fk_usuario_empresa CHECK (empresa IS NULL OR EXISTS (SELECT 1 FROM public.empresas e WHERE e.codigo = empresa));
ALTER TABLE public.reg_consulta ADD CONSTRAINT fk_consulta_usuario CHECK (usuario IN (SELECT perfil_id FROM public.usuarios));

-- ============================================================================
-- SECUENCIAS PARA ARREGLO DE LLAVES PRIMARIAS SERIAL
-- ============================================================================

ALTER SEQUENCE public.ventas_id_seq OWNED BY public.ventas.id;
ALTER SEQUENCE public.detalle_reg_consulta_id_seq OWNED BY public.detalle_reg_consulta.id;
ALTER SEQUENCE public.archivos_id_seq OWNED BY public.archivos.id;
ALTER SEQUENCE public.auditoria_id_seq OWNED BY public.auditoria.id;

-- ============================================================================
-- PERMISOS Y ROLES
-- ============================================================================

-- Si tienes roles específicos, puedes agregarlos aquí
-- Ejemplo: GRANT USAGE, SELECT ON ALL SEQUENCES TO app_read_only_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_admin_user;

-- ============================================================================
-- VISTAS MATERIALIZADAS (OPCIONAL - PARA MEJOR RENDIMIENTO)
-- ============================================================================

-- Vista consolidada de estadísticas mensuales
CREATE VIEW IF NOT EXISTS public.vw_estadisticas_empresas AS
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

COMMENT ON VIEW public.vw_estadisticas_empresas IS 'Vista para reportes de actividad por empresa';

-- ================================================================
-- COMENTARIO FINAL DEL SCRIPT
-- ================================================================

COMMENT ON DATABASE current_database() IS 'Base de datos de gestión de consultas y ventas - Sistema Django + PostgreSQL';

-- ================================================================
-- FIN DEL SCRIPT DE CREACIÓN
-- ================================================================