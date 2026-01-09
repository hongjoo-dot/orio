-- ============================================
-- [필수 인덱스] Power BI Direct Query 핵심 최적화
-- 생성일: 2025-12-31
-- 총 19개 인덱스
-- ============================================

USE oriodatabase;
GO

-- ============================================
-- 1. Product - BrandID FK (모든 제품 JOIN에 필수)
-- ============================================
PRINT '[1/19] Product.BrandID...';
CREATE NONCLUSTERED INDEX IX_Product_BrandID
    ON dbo.Product (BrandID);
GO

-- ============================================
-- 2. ProductBox - ProductID FK (BOM JOIN 필수)
-- ============================================
PRINT '[2/19] ProductBox.ProductID...';
CREATE NONCLUSTERED INDEX IX_ProductBox_ProductID
    ON dbo.ProductBox (ProductID);
GO

-- ============================================
-- 3-6. ProductBOM - 인덱스 전무 (BOM 전개 쿼리 필수)
-- ============================================
PRINT '[3/19] ProductBOM.ParentProductBoxID...';
CREATE NONCLUSTERED INDEX IX_ProductBOM_ParentBoxID
    ON dbo.ProductBOM (ParentProductBoxID);

PRINT '[4/19] ProductBOM.ChildProductBoxID...';
CREATE NONCLUSTERED INDEX IX_ProductBOM_ChildBoxID
    ON dbo.ProductBOM (ChildProductBoxID);

PRINT '[5/19] ProductBOM.ParentProductID...';
CREATE NONCLUSTERED INDEX IX_ProductBOM_ParentProductID
    ON dbo.ProductBOM (ParentProductID);

PRINT '[6/19] ProductBOM.ChildProductID...';
CREATE NONCLUSTERED INDEX IX_ProductBOM_ChildProductID
    ON dbo.ProductBOM (ChildProductID);
GO

-- ============================================
-- 7-8. Channel - 자주 사용하는 필터
-- ============================================
PRINT '[7/19] Channel.LiveSource...';
CREATE NONCLUSTERED INDEX IX_Channel_LiveSource
    ON dbo.Channel (LiveSource);

PRINT '[8/19] Channel.SabangnetMallID...';
CREATE NONCLUSTERED INDEX IX_Channel_SabangnetMallID
    ON dbo.Channel (SabangnetMallID);
GO

-- ============================================
-- 9. ChannelDetail - ChannelID FK
-- ============================================
PRINT '[9/19] ChannelDetail.ChannelID...';
CREATE NONCLUSTERED INDEX IX_ChannelDetail_ChannelID
    ON dbo.ChannelDetail (ChannelID);
GO

-- ============================================
-- 10-12. ERPSales - 날짜+FK 복합 커버링 인덱스 (핵심!)
-- Power BI 매출 리포트 성능에 직접 영향
-- ============================================
PRINT '[10/19] ERPSales (DATE, ChannelID) + covering...';
CREATE NONCLUSTERED INDEX IX_ERPSales_Date_Channel
    ON dbo.ERPSales ([DATE], ChannelID)
    INCLUDE (Quantity, TaxableAmount);

PRINT '[11/19] ERPSales (DATE, ProductID) + covering...';
CREATE NONCLUSTERED INDEX IX_ERPSales_Date_Product
    ON dbo.ERPSales ([DATE], ProductID)
    INCLUDE (Quantity, TaxableAmount);

PRINT '[12/19] ERPSales (DATE, BrandID) + covering...';
CREATE NONCLUSTERED INDEX IX_ERPSales_Date_Brand
    ON dbo.ERPSales ([DATE], BrandID)
    INCLUDE (Quantity, TaxableAmount);
GO

-- ============================================
-- 13-14. OrdersRealtime - 커버링 인덱스 (실시간 대시보드 핵심)
-- ============================================
PRINT '[13/19] OrdersRealtime (BrandID, OrderDate) + covering...';
-- 기존 인덱스 삭제 후 커버링으로 재생성
IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_OrdersRT_BrandID' AND object_id = OBJECT_ID('dbo.OrdersRealtime'))
    DROP INDEX IX_OrdersRT_BrandID ON dbo.OrdersRealtime;

CREATE NONCLUSTERED INDEX IX_OrdersRT_BrandID_Covering
    ON dbo.OrdersRealtime (BrandID, OrderDate)
    INCLUDE (OrderQuantity, OrderAmount, OrderPrice);

PRINT '[14/19] OrdersRealtime.SourceChannel...';
CREATE NONCLUSTERED INDEX IX_OrdersRT_SourceChannel
    ON dbo.OrdersRealtime (SourceChannel, OrderDate);
GO

-- ============================================
-- 15-16. SabangnetOrders - 파이프라인 필터 조건
-- ============================================
PRINT '[15/19] SabangnetOrders.ProductID...';
CREATE NONCLUSTERED INDEX IX_SabangnetOrders_ProductID
    ON dbo.SabangnetOrders (ProductID);

PRINT '[16/19] SabangnetOrders.DELIVERY_CONFIRM_DATE...';
CREATE NONCLUSTERED INDEX IX_SabangnetOrders_DeliveryConfirmDate
    ON dbo.SabangnetOrders (DELIVERY_CONFIRM_DATE);
GO

-- ============================================
-- 17. Cafe24Orders - 출고일 필터 (파이프라인 조건)
-- ============================================
PRINT '[17/19] Cafe24Orders.shipped_date...';
CREATE NONCLUSTERED INDEX IX_Cafe24Orders_shipped_date
    ON dbo.Cafe24Orders (shipped_date);
GO

-- ============================================
-- 18. AdDataMeta - 계정+날짜 복합 (광고 리포트 핵심)
-- ============================================
PRINT '[18/19] AdDataMeta (AccountName, Date) + covering...';
CREATE NONCLUSTERED INDEX IX_AdDataMeta_AccountName_Date
    ON dbo.AdDataMeta (AccountName, [Date])
    INCLUDE (Spend, SpendKRW, Purchase, PurchaseValue);
GO

-- ============================================
-- 19. NaverAdsSearchVolume - 브랜드+날짜 복합
-- ============================================
PRINT '[19/19] NaverAdsSearchVolume (BrandID, CollectionDate)...';
CREATE NONCLUSTERED INDEX IX_NaverAdsSearchVolume_Brand_Date
    ON dbo.NaverAdsSearchVolume (BrandID, CollectionDate);
GO

-- ============================================
-- 완료
-- ============================================
PRINT '';
PRINT '============================================';
PRINT '[필수 인덱스] 19개 생성 완료!';
PRINT '============================================';
PRINT '';
PRINT 'Power BI에서 속도 테스트 후,';
PRINT '여전히 느리면 indexes_optional.sql 실행';
PRINT '============================================';
GO
