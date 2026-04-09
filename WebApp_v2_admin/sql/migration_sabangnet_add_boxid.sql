-- ============================================================
-- SabangnetInventorySnapshot, LocationSnapshot에 BoxID 추가
-- + 기존 데이터 백필 (ProductCode = ERPCode 기준)
-- ============================================================

-- 1. 컬럼 추가
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('SabangnetInventorySnapshot') AND name = 'BoxID')
    ALTER TABLE [dbo].[SabangnetInventorySnapshot] ADD BoxID INT NULL;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('SabangnetLocationSnapshot') AND name = 'BoxID')
    ALTER TABLE [dbo].[SabangnetLocationSnapshot] ADD BoxID INT NULL;

PRINT N'✅ BoxID 컬럼 추가 완료';
GO

-- 2. 기존 데이터 백필: ProductCode(= manage_code2 = ERPCode) 기준으로 BoxID 매핑
UPDATE s
SET s.BoxID = pb.BoxID
FROM [dbo].[SabangnetInventorySnapshot] s
JOIN [dbo].[ProductBox] pb ON RTRIM(s.ProductCode) = RTRIM(pb.ERPCode)
WHERE s.BoxID IS NULL;

PRINT N'✅ InventorySnapshot BoxID 백필 완료: ' + CAST(@@ROWCOUNT AS NVARCHAR);
GO

UPDATE s
SET s.BoxID = pb.BoxID
FROM [dbo].[SabangnetLocationSnapshot] s
JOIN [dbo].[ProductBox] pb ON RTRIM(s.ShippingProductID) = RTRIM(pb.ERPCode)
WHERE s.BoxID IS NULL;

-- LocationSnapshot은 ProductCode가 없으므로 InventorySnapshot 경유
UPDATE ls
SET ls.BoxID = inv.BoxID
FROM [dbo].[SabangnetLocationSnapshot] ls
JOIN [dbo].[SabangnetInventorySnapshot] inv
    ON ls.ShippingProductID = inv.ShippingProductID
    AND ls.SnapshotDate = inv.SnapshotDate
    AND ls.SnapshotTime = inv.SnapshotTime
WHERE ls.BoxID IS NULL AND inv.BoxID IS NOT NULL;

PRINT N'✅ LocationSnapshot BoxID 백필 완료: ' + CAST(@@ROWCOUNT AS NVARCHAR);
GO