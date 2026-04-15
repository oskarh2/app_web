-- ================================================================
-- SCRIPT SQL CORREGIDO - VISTA DE ESTADÍSTICAS
-- ================================================================

DROP VIEW IF EXISTS public.vw_estadisticas_empresas;

CREATE OR REPLACE VIEW public.vw_estadisticas_empresas AS
SELECT 
    e.codigo AS empresa_id,
    e.nombre AS empresa_nombre,
    e.nit AS nit,
    COUNT(DISTINCT r.consulta_id) AS total_consultas,
    COUNT(DISTINCT a.id) AS total_archivos,          -- Cuenta archivos por consulta vinculada
    SUM(COALESCE(v.cantidad, 0)) AS total_ventas,   -- Agrega ventas de la misma empresa
    SUM(COALESCE(v.monto_total, 0)) AS total_monto_ventas,
    MIN(r.fecha_hora) AS primera_consulta,
    MAX(r.fecha_hora) AS ultima_consulta
FROM public.empresas e
LEFT JOIN public.reg_consulta r ON e.codigo = r.empresa
LEFT JOIN public.archivos a ON r.consulta_id = a.consulta_id     -- ✅ Unir a través de reg_consulta
LEFT JOIN public.ventas v ON e.codigo = v.empresa               -- ✅ Ventas también son directas
GROUP BY e.codigo, e.nombre, e.nit;

COMMENT ON VIEW public.vw_estadisticas_empresas IS 'Reporte de actividad consolidado por empresa';
