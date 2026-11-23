import psycopg
from psycopg.rows import dict_row
import json
import os

# Connect to database using local env or direct URL
conn = psycopg.connect('postgresql://postgres:postgres@localhost:5432/acc_rmc_prod', row_factory=dict_row)
cur = conn.cursor()

results = {}

# 1. PRD_BATCH_MATERIAL_CONSUMPTIONS OVERVIEW
cur.execute('''
SELECT 
    COUNT(*) as total_rows, 
    COUNT(DISTINCT batch_id) as distinct_batches, 
    MIN(created_at) as min_date, 
    MAX(created_at) as max_date 
FROM prd_batch_material_consumptions
''')
results['overview'] = cur.fetchone()

# 2. COLUMN NULL RATES
cur.execute('''
SELECT 
    COUNT(*) as total,
    COUNT(planned_quantity) as cnt_planned,
    COUNT(actual_quantity) as cnt_actual,
    COUNT(variance_quantity) as cnt_var_qty,
    COUNT(variance_percentage) as cnt_var_pct,
    COUNT(actual_quantity_kg) as cnt_actual_kg,
    COUNT(planned_quantity_kg) as cnt_planned_kg,
    COUNT(quantity_kg_per_m3) as cnt_kg_per_m3,
    COUNT(moisture_percentage) as cnt_moisture,
    COUNT(absorption_percentage) as cnt_absorption,
    COUNT(moisture_correction_kg) as cnt_moist_corr
FROM prd_batch_material_consumptions
''')
results['null_rates'] = cur.fetchone()

# 3. MATERIAL TAXONOMY & CATEGORIES
cur.execute('''
SELECT 
    mc.category_code,
    mc.category_name,
    m.material_code,
    m.material_name,
    m.unit_of_measure,
    COUNT(pmc.consumption_id) as usage_count,
    ROUND(AVG(pmc.planned_quantity::numeric), 2) as avg_planned,
    ROUND(AVG(pmc.actual_quantity::numeric), 2) as avg_actual,
    ROUND(AVG(pmc.variance_percentage::numeric), 2) as avg_var_pct
FROM mst_materials m
JOIN mst_material_categories mc ON m.category_id = mc.category_id
LEFT JOIN prd_batch_material_consumptions pmc ON m.material_id = pmc.material_id
GROUP BY mc.category_code, mc.category_name, m.material_code, m.material_name, m.unit_of_measure
ORDER BY mc.category_code, usage_count DESC;
''')
results['taxonomy'] = cur.fetchall()

# 4. BATCH WEIGHMENT VARIANCE COMPLIANCE (IS 4926)
cur.execute('''
SELECT 
    mc.category_code,
    COUNT(pmc.consumption_id) as total_records,
    SUM(CASE 
        WHEN mc.category_code IN ('CEMENT', 'BINDER', 'GGBS', 'FLY_ASH', 'SILICA_FUME') AND ABS(pmc.variance_percentage) <= 2.0 THEN 1
        WHEN mc.category_code NOT IN ('CEMENT', 'BINDER', 'GGBS', 'FLY_ASH', 'SILICA_FUME') AND ABS(pmc.variance_percentage) <= 3.0 THEN 1
        ELSE 0 
    END) as compliant_records,
    ROUND(AVG(ABS(pmc.variance_percentage))::numeric, 3) as mean_abs_variance_pct,
    ROUND(MIN(pmc.variance_percentage)::numeric, 3) as min_variance_pct,
    ROUND(MAX(pmc.variance_percentage)::numeric, 3) as max_variance_pct
FROM prd_batch_material_consumptions pmc
JOIN mst_materials m ON pmc.material_id = m.material_id
JOIN mst_material_categories mc ON m.category_id = mc.category_id
GROUP BY mc.category_code;
''')
results['is4926_compliance'] = cur.fetchall()

# 5. W/C AND W/B RATIO AUDIT (BATCH LEVEL)
cur.execute('''
WITH batch_binders_water AS (
    SELECT 
        b.batch_id,
        b.batch_number,
        r.recipe_code,
        r.target_strength_mpa,
        r.water_cement_ratio as design_wc,
        b.actual_quantity_m3,
        SUM(CASE WHEN mc.category_code = 'CEMENT' THEN pmc.actual_quantity ELSE 0 END) as actual_cement_kg,
        SUM(CASE WHEN mc.category_code IN ('CEMENT', 'GGBS', 'FLY_ASH', 'SILICA_FUME', 'BINDER') THEN pmc.actual_quantity ELSE 0 END) as actual_binder_kg,
        SUM(CASE WHEN mc.category_code = 'WATER' THEN pmc.actual_quantity ELSE 0 END) as actual_water_kg,
        SUM(CASE WHEN mc.category_code = 'CEMENT' THEN pmc.planned_quantity ELSE 0 END) as planned_cement_kg,
        SUM(CASE WHEN mc.category_code IN ('CEMENT', 'GGBS', 'FLY_ASH', 'SILICA_FUME', 'BINDER') THEN pmc.planned_quantity ELSE 0 END) as planned_binder_kg,
        SUM(CASE WHEN mc.category_code = 'WATER' THEN pmc.planned_quantity ELSE 0 END) as planned_water_kg
    FROM prd_batches b
    JOIN mst_recipes r ON b.recipe_id = r.recipe_id
    JOIN prd_batch_material_consumptions pmc ON b.batch_id = pmc.batch_id
    JOIN mst_materials m ON pmc.material_id = m.material_id
    JOIN mst_material_categories mc ON m.category_id = mc.category_id
    GROUP BY b.batch_id, b.batch_number, r.recipe_code, r.target_strength_mpa, r.water_cement_ratio, b.actual_quantity_m3
)
SELECT 
    COUNT(*) as total_batches,
    COUNT(CASE WHEN actual_binder_kg > 0 AND actual_water_kg > 0 THEN 1 END) as valid_wb_batches,
    ROUND(AVG(CASE WHEN actual_cement_kg > 0 THEN actual_water_kg / actual_cement_kg END)::numeric, 4) as avg_actual_wc,
    ROUND(AVG(CASE WHEN actual_binder_kg > 0 THEN actual_water_kg / actual_binder_kg END)::numeric, 4) as avg_actual_wb,
    ROUND(AVG(CASE WHEN planned_binder_kg > 0 THEN planned_water_kg / planned_binder_kg END)::numeric, 4) as avg_planned_wb,
    ROUND(AVG(design_wc)::numeric, 4) as avg_design_wc
FROM batch_binders_water;
''')
results['wc_wb_stats'] = cur.fetchone()

# 6. BINDER EFFICIENCY AUDIT (kg/m3 per MPa)
cur.execute('''
WITH batch_eff AS (
    SELECT 
        b.batch_id,
        r.recipe_code,
        r.target_strength_mpa,
        AVG(t.break_force_kn / 22.5) as actual_28d_mpa,
        SUM(CASE WHEN mc.category_code = 'CEMENT' THEN pmc.actual_quantity ELSE 0 END) / NULLIF(b.actual_quantity_m3, 0) as cement_kg_per_m3,
        SUM(CASE WHEN mc.category_code IN ('CEMENT', 'GGBS', 'FLY_ASH', 'SILICA_FUME', 'BINDER') THEN pmc.actual_quantity ELSE 0 END) / NULLIF(b.actual_quantity_m3, 0) as binder_kg_per_m3
    FROM prd_batches b
    JOIN mst_recipes r ON b.recipe_id = r.recipe_id
    JOIN prd_batch_material_consumptions pmc ON b.batch_id = pmc.batch_id
    JOIN mst_materials m ON pmc.material_id = m.material_id
    JOIN mst_material_categories mc ON m.category_id = mc.category_id
    LEFT JOIN qc_cube_tests t ON b.batch_id = t.batch_id AND t.test_age_days = 28 AND t.break_force_kn > 0
    GROUP BY b.batch_id, r.recipe_code, r.target_strength_mpa, b.actual_quantity_m3
)
SELECT 
    COUNT(*) as total_batches,
    COUNT(CASE WHEN actual_28d_mpa IS NOT NULL THEN 1 END) as tested_batches,
    ROUND(AVG(binder_kg_per_m3)::numeric, 2) as avg_binder_density,
    ROUND(AVG(cement_kg_per_m3)::numeric, 2) as avg_cement_density,
    ROUND(AVG(CASE WHEN actual_28d_mpa > 0 THEN binder_kg_per_m3 / actual_28d_mpa END)::numeric, 2) as avg_kg_per_m3_per_actual_mpa,
    ROUND(AVG(binder_kg_per_m3 / target_strength_mpa)::numeric, 2) as avg_kg_per_m3_per_target_mpa
FROM batch_eff;
''')
results['binder_efficiency'] = cur.fetchone()

print(json.dumps(results, default=str, indent=2))
conn.close()
