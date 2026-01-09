-- ============================================
-- [추가 인덱스] 필수 인덱스 적용 후에도 느릴 때 사용
-- 생성일: 2025-12-31
-- 총 28개 인덱스
-- ============================================

USE oriodatabase;
GO

PRINT '============================================';
PRINT '[추가 인덱스] 시작';
PRINT '============================================';
PRINT '';

-- ============================================
-- Channel - 추가 필터용
-- ============================================
PRINT 'Channel 추가 인덱스...';

CREATE NONCLUSTERED INDEX IX_Channel_Group
    ON dbo.Channel ([Group]);

CREATE NONCLUSTERED INDEX IX_Channel_Type
    ON dbo.Channel ([Type]);
GO

-- ============================================
-- Product - 추가 필터용
-- ============================================
PRINT 'Product 추가 인덱스...';

CREATE NONCLUSTERED INDEX IX_Product_TypeDB
    ON dbo.Product (TypeDB);

CREATE NONCLUSTERED INDEX IX_Product_Status
    ON dbo.Product (Status);

CREATE NONCLUSTERED INDEX IX_Product_SabangnetCode
    ON dbo.Product (SabangnetCode);

CREATE NONCLUSTERED INDEX IX_Product_BaseBarcode
    ON dbo.Product (BaseBarcode);
GO

-- ============================================
-- ChannelDetail - BizNumber 검색
-- ============================================
PRINT 'ChannelDetail 추가 인덱스...';

CREATE NONCLUSTERED INDEX IX_ChannelDetail_BizNumber
    ON dbo.ChannelDetail (BizNumber);
GO

-- ============================================
-- ERPSales - 추가 필터용
-- ============================================
PRINT 'ERPSales 추가 인덱스...';

CREATE NONCLUSTERED INDEX IX_ERPSales_TransactionType
    ON dbo.ERPSales (TransactionType);

CREATE NONCLUSTERED INDEX IX_ERPSales_WarehouseID
    ON dbo.ERPSales (WarehouseID);

CREATE NONCLUSTERED INDEX IX_ERPSales_ChannelDetailID
    ON dbo.ERPSales (ChannelDetailID);
GO

-- ============================================
-- OrdersRealtime - 추가 필터용
-- ============================================
PRINT 'OrdersRealtime 추가 인덱스...';

CREATE NONCLUSTERED INDEX IX_OrdersRT_OrderStatus
    ON dbo.OrdersRealtime (OrderStatus);

CREATE NONCLUSTERED INDEX IX_OrdersRT_ShippedDate
    ON dbo.OrdersRealtime (ShippedDate);

CREATE NONCLUSTERED INDEX IX_OrdersRT_SabangnetIDX
    ON dbo.OrdersRealtime (SabangnetIDX);

CREATE NONCLUSTERED INDEX IX_OrdersRT_SourceOrderID
    ON dbo.OrdersRealtime (SourceOrderID);
GO

-- ============================================
-- SabangnetOrders - 추가 필터용
-- ============================================
PRINT 'SabangnetOrders 추가 인덱스...';

CREATE NONCLUSTERED INDEX IX_SabangnetOrders_OrderStatus
    ON dbo.SabangnetOrders (ORDER_STATUS);

CREATE NONCLUSTERED INDEX IX_SabangnetOrders_MallID
    ON dbo.SabangnetOrders (MALL_ID);
GO

-- ============================================
-- Cafe24Orders - 추가 필터용
-- ============================================
PRINT 'Cafe24Orders 추가 인덱스...';

CREATE NONCLUSTERED INDEX IX_Cafe24Orders_order_status
    ON dbo.Cafe24Orders (order_status);
GO

-- ============================================
-- Cafe24OrdersDetail - order_status 필터
-- ============================================
PRINT 'Cafe24OrdersDetail 추가 인덱스...';

CREATE NONCLUSTERED INDEX IX_Cafe24OrdersDetail_order_status
    ON dbo.Cafe24OrdersDetail (order_status);
GO

-- ============================================
-- AdDataMeta - CampaignID 필터
-- ============================================
PRINT 'AdDataMeta 추가 인덱스...';

CREATE NONCLUSTERED INDEX IX_AdDataMeta_CampaignID
    ON dbo.AdDataMeta (CampaignID);
GO

-- ============================================
-- AdDataMetaBreakdown - 분석용
-- ============================================
PRINT 'AdDataMetaBreakdown 추가 인덱스...';

CREATE NONCLUSTERED INDEX IX_AdDataMetaBreakdown_AccountName_Date
    ON dbo.AdDataMetaBreakdown (AccountName, [Date]);

CREATE NONCLUSTERED INDEX IX_AdDataMetaBreakdown_Age_Gender
    ON dbo.AdDataMetaBreakdown (Age, Gender, [Date]);
GO

-- ============================================
-- AdDataNaver - CampaignID 필터
-- ============================================
PRINT 'AdDataNaver 추가 인덱스...';

CREATE NONCLUSTERED INDEX IX_AdDataNaver_CampaignID
    ON dbo.AdDataNaver (CampaignID);
GO

-- ============================================
-- GoogleAdsSearchVolume - 추가 필터용
-- ============================================
PRINT 'GoogleAdsSearchVolume 추가 인덱스...';

CREATE NONCLUSTERED INDEX IX_GoogleAds_BrandID
    ON dbo.GoogleAdsSearchVolume (BrandID);

CREATE NONCLUSTERED INDEX IX_GoogleAds_CollectionDate
    ON dbo.GoogleAdsSearchVolume (CollectionDate);
GO

-- ============================================
-- NaverAdsSearchVolume - 추가 필터용
-- ============================================
PRINT 'NaverAdsSearchVolume 추가 인덱스...';

CREATE NONCLUSTERED INDEX IX_NaverAdsSearchVolume_KeywordID
    ON dbo.NaverAdsSearchVolume (KeywordID);

CREATE NONCLUSTERED INDEX IX_NaverAdsSearchVolume_Keyword
    ON dbo.NaverAdsSearchVolume (Keyword);
GO

-- ============================================
-- AdDataNaver_Frog - CampaignID 필터
-- ============================================
PRINT 'AdDataNaver_Frog 추가 인덱스...';

IF OBJECT_ID('dbo.AdDataNaver_Frog', 'U') IS NOT NULL
BEGIN
    CREATE NONCLUSTERED INDEX IX_AdDataNaver_Frog_CampaignID
        ON dbo.AdDataNaver_Frog (CampaignID);
END
GO

-- ============================================
-- AdContractNaver - IsActive 필터
-- ============================================
PRINT 'AdContractNaver 추가 인덱스...';

IF OBJECT_ID('dbo.AdContractNaver', 'U') IS NOT NULL
BEGIN
    CREATE NONCLUSTERED INDEX IX_AdContractNaver_IsActive
        ON dbo.AdContractNaver (IsActive, StartDate, EndDate);
END
GO

-- ============================================
-- 완료
-- ============================================
PRINT '';
PRINT '============================================';
PRINT '[추가 인덱스] 28개 생성 완료!';
PRINT '============================================';
PRINT '';
PRINT '전체 인덱스: 필수(19) + 추가(28) = 47개';
PRINT '============================================';
GO
