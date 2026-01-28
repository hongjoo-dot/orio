-- =====================================================
-- StartTime / EndTime 기본값 변경
-- StartTime: 00:00:00 (그날 시작)
-- EndTime:   23:59:59 (그날 끝)
-- 변수 없이 동적 SQL로 처리
-- =====================================================

-- 1. Promotion.StartTime DEFAULT (00:00:00)
EXEC(N'
DECLARE @C NVARCHAR(200);
SELECT @C = dc.name
FROM sys.default_constraints dc
JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
WHERE dc.parent_object_id = OBJECT_ID(''dbo.Promotion'') AND c.name = ''StartTime'';
IF @C IS NOT NULL EXEC(''ALTER TABLE [dbo].[Promotion] DROP CONSTRAINT ['' + @C + '']'');
');
ALTER TABLE [dbo].[Promotion] ADD DEFAULT '00:00:00' FOR [StartTime];
PRINT N'[OK] Promotion.StartTime DEFAULT = 00:00:00';

-- 2. Promotion.EndTime DEFAULT (23:59:59)
EXEC(N'
DECLARE @C NVARCHAR(200);
SELECT @C = dc.name
FROM sys.default_constraints dc
JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
WHERE dc.parent_object_id = OBJECT_ID(''dbo.Promotion'') AND c.name = ''EndTime'';
IF @C IS NOT NULL EXEC(''ALTER TABLE [dbo].[Promotion] DROP CONSTRAINT ['' + @C + '']'');
');
ALTER TABLE [dbo].[Promotion] ADD DEFAULT '23:59:59' FOR [EndTime];
PRINT N'[OK] Promotion.EndTime DEFAULT = 23:59:59';

-- 3. TargetPromotionProduct.StartTime DEFAULT (00:00:00)
EXEC(N'
DECLARE @C NVARCHAR(200);
SELECT @C = dc.name
FROM sys.default_constraints dc
JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
WHERE dc.parent_object_id = OBJECT_ID(''dbo.TargetPromotionProduct'') AND c.name = ''StartTime'';
IF @C IS NOT NULL EXEC(''ALTER TABLE [dbo].[TargetPromotionProduct] DROP CONSTRAINT ['' + @C + '']'');
');
ALTER TABLE [dbo].[TargetPromotionProduct] ADD DEFAULT '00:00:00' FOR [StartTime];
PRINT N'[OK] TargetPromotionProduct.StartTime DEFAULT = 00:00:00';

-- 4. TargetPromotionProduct.EndTime DEFAULT (23:59:59)
EXEC(N'
DECLARE @C NVARCHAR(200);
SELECT @C = dc.name
FROM sys.default_constraints dc
JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
WHERE dc.parent_object_id = OBJECT_ID(''dbo.TargetPromotionProduct'') AND c.name = ''EndTime'';
IF @C IS NOT NULL EXEC(''ALTER TABLE [dbo].[TargetPromotionProduct] DROP CONSTRAINT ['' + @C + '']'');
');
ALTER TABLE [dbo].[TargetPromotionProduct] ADD DEFAULT '23:59:59' FOR [EndTime];
PRINT N'[OK] TargetPromotionProduct.EndTime DEFAULT = 23:59:59';
