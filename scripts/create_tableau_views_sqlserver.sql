CREATE OR ALTER VIEW dbo.vw_mes_orders_dashboard AS
SELECT
    id,
    order_code,
    product_name,
    order_qty,
    completed_qty,
    CAST(order_qty - completed_qty AS int) AS remaining_qty,
    priority,
    status,
    create_time,
    update_time
FROM dbo.plan_ordermain
WHERE ISNULL(del_flag, 0) = 0;
GO

CREATE OR ALTER VIEW dbo.vw_mes_craft_routes AS
SELECT
    id,
    craft_code,
    craft_name,
    product_type,
    status,
    create_time,
    steps_json
FROM dbo.base_craft
WHERE ISNULL(del_flag, 0) = 0;
GO

CREATE OR ALTER VIEW dbo.vw_mes_equipment_status AS
SELECT
    id,
    eq_code,
    eq_name,
    eq_type,
    status,
    create_time
FROM dbo.base_equipment
WHERE ISNULL(del_flag, 0) = 0;
GO

CREATE OR ALTER VIEW dbo.vw_mes_yield_trend AS
SELECT
    id,
    lot_code,
    product_name,
    step_name,
    total_qty,
    pass_qty,
    defect_qty,
    yield_pct,
    inspect_time
FROM dbo.iqc_yield
WHERE ISNULL(del_flag, 0) = 0;
GO
