IF COL_LENGTH('dbo.plugin_datasource_link','database_name') IS NULL
    ALTER TABLE dbo.plugin_datasource_link ADD database_name nvarchar(64) NULL;
GO
IF COL_LENGTH('dbo.plugin_datasource_link','invokes') IS NULL
    ALTER TABLE dbo.plugin_datasource_link ADD invokes int NULL;
GO
IF COL_LENGTH('dbo.plugin_datasource_link','create_by_id') IS NULL
    ALTER TABLE dbo.plugin_datasource_link ADD create_by_id nvarchar(64) NULL;
GO
IF COL_LENGTH('dbo.plugin_datasource_link','update_by_id') IS NULL
    ALTER TABLE dbo.plugin_datasource_link ADD update_by_id nvarchar(64) NULL;
GO
IF COL_LENGTH('dbo.plugin_datasource_link','tenant_id') IS NULL
    ALTER TABLE dbo.plugin_datasource_link ADD tenant_id nvarchar(64) NULL;
GO
UPDATE dbo.plugin_datasource_link
SET
    database_name = ISNULL(database_name, db_name),
    create_by_id = ISNULL(create_by_id, create_by),
    update_by_id = ISNULL(update_by_id, update_by),
    invokes = ISNULL(invokes, 0);
GO
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME='plugin_datasource_link'
ORDER BY ORDINAL_POSITION;
GO
