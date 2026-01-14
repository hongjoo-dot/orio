-- ============================================
-- 행사 관리 시스템 - View
-- ============================================

-- ============================================
-- 1. 온라인 행사 View
-- ============================================
CREATE VIEW vw_PromotionOnline AS
SELECT
    p.PromotionID,
    p.PromotionName,
    p.PromotionType,
    p.StartDate,
    p.EndDate,
    p.Status,

    -- 브랜드 정보
    p.BrandID,
    b.BrandName,

    -- 채널 정보
    p.ChannelNames,
    p.CommissionRate,

    -- 할인 분담
    p.DiscountOwner,
    p.OrioShare,
    p.ChannelShare,

    -- 상품 정보
    pp.PromotionProductID,
    pp.ProductID,
    prod.ProductName,
    prod.ProductCode,

    -- 가격 구조
    pp.RegularPrice,
    pp.SellingPrice,
    pp.PromotionPrice,
    pp.SupplyPrice,
    pp.UnitCost,

    -- 할인율
    pp.DiscountRate,
    pp.CouponDiscountRate,

    -- 비용
    pp.SettlementType,
    pp.LogisticsCost,
    pp.ManagementCost,
    pp.WarehouseCost,

    -- 마진 계산
    pp.MarginRate,
    pp.MarginAmount,

    -- 실제 마진 계산 (온라인 - 위탁 고려)
    CASE
        WHEN pp.SettlementType = N'CONSIGNMENT' THEN
            -- 위탁: 판매가 - 원가 - 수수료 - 물류비 - 관리비 - 창고비
            pp.PromotionPrice
            - ISNULL(pp.UnitCost, 0)
            - (pp.PromotionPrice * ISNULL(p.CommissionRate, 0) / 100)
            - ISNULL(pp.LogisticsCost, 0)
            - ISNULL(pp.ManagementCost, 0)
            - ISNULL(pp.WarehouseCost, 0)
        ELSE
            -- 완사입: 판매가 - 원가 - 물류비 - 관리비 - 창고비
            pp.PromotionPrice
            - ISNULL(pp.UnitCost, 0)
            - ISNULL(pp.LogisticsCost, 0)
            - ISNULL(pp.ManagementCost, 0)
            - ISNULL(pp.WarehouseCost, 0)
    END AS CalculatedMarginAmount,

    -- 실제 마진율 계산
    CASE
        WHEN pp.PromotionPrice > 0 THEN
            CASE
                WHEN pp.SettlementType = N'CONSIGNMENT' THEN
                    ((pp.PromotionPrice
                      - ISNULL(pp.UnitCost, 0)
                      - (pp.PromotionPrice * ISNULL(p.CommissionRate, 0) / 100)
                      - ISNULL(pp.LogisticsCost, 0)
                      - ISNULL(pp.ManagementCost, 0)
                      - ISNULL(pp.WarehouseCost, 0)
                    ) / pp.PromotionPrice) * 100
                ELSE
                    ((pp.PromotionPrice
                      - ISNULL(pp.UnitCost, 0)
                      - ISNULL(pp.LogisticsCost, 0)
                      - ISNULL(pp.ManagementCost, 0)
                      - ISNULL(pp.WarehouseCost, 0)
                    ) / pp.PromotionPrice) * 100
            END
        ELSE NULL
    END AS CalculatedMarginRate,

    -- 목표
    pp.TargetSalesAmount,
    pp.TargetQuantity,
    pp.TargetProfit,
    pp.RequiredStockQty,

    -- 기타
    p.Notes AS PromotionNotes,
    pp.Notes AS ProductNotes,
    p.CreatedDate,
    p.UpdatedDate

FROM dbo.Promotion p
INNER JOIN dbo.PromotionProduct pp ON p.PromotionID = pp.PromotionID
INNER JOIN dbo.Brand b ON p.BrandID = b.BrandID
INNER JOIN dbo.Product prod ON pp.ProductID = prod.ProductID
WHERE p.ChannelType = N'ONLINE';

-- ============================================
-- 2. 오프라인 행사 View
-- ============================================
CREATE VIEW vw_PromotionOffline AS
SELECT
    p.PromotionID,
    p.PromotionName,
    p.PromotionType,
    p.StartDate,
    p.EndDate,
    p.Status,

    -- 브랜드 정보
    p.BrandID,
    b.BrandName,

    -- 채널 정보
    p.ChannelNames,

    -- 할인 분담
    p.DiscountOwner,
    p.OrioShare,
    p.ChannelShare,

    -- 오프라인 전용
    p.BundleCondition,

    -- 상품 정보
    pp.PromotionProductID,
    pp.ProductID,
    prod.ProductName,
    prod.ProductCode,

    -- 가격 구조
    pp.RegularPrice,
    pp.SellingPrice,
    pp.PromotionPrice,
    pp.SupplyPrice,
    pp.UnitCost,

    -- 할인
    pp.DiscountRate,

    -- 원매가 할인액 계산
    CASE
        WHEN p.PromotionType = N'WHOLESALE_DISCOUNT' THEN
            ISNULL(pp.SellingPrice, 0) - ISNULL(pp.SupplyPrice, 0)
        ELSE NULL
    END AS WholesalePriceDiscount,

    -- 비용
    pp.SettlementType,
    pp.LogisticsCost,
    pp.ManagementCost,
    pp.WarehouseCost,

    -- 마진 계산
    pp.MarginRate,
    pp.MarginAmount,

    -- 실제 마진 계산 (오프라인 - 주로 완사입)
    CASE
        WHEN pp.SettlementType = N'DIRECT' THEN
            -- 완사입: 공급가 - 원가 - 물류비 - 관리비 - 창고비
            ISNULL(pp.SupplyPrice, 0)
            - ISNULL(pp.UnitCost, 0)
            - ISNULL(pp.LogisticsCost, 0)
            - ISNULL(pp.ManagementCost, 0)
            - ISNULL(pp.WarehouseCost, 0)
        ELSE
            -- 위탁: 판매가 - 원가 - 수수료 - 물류비
            pp.PromotionPrice
            - ISNULL(pp.UnitCost, 0)
            - (pp.PromotionPrice * ISNULL(p.CommissionRate, 0) / 100)
            - ISNULL(pp.LogisticsCost, 0)
            - ISNULL(pp.ManagementCost, 0)
            - ISNULL(pp.WarehouseCost, 0)
    END AS CalculatedMarginAmount,

    -- 실제 마진율 계산
    CASE
        WHEN pp.SettlementType = N'DIRECT' AND pp.SupplyPrice > 0 THEN
            -- 완사입: 공급가 기준 마진율
            ((ISNULL(pp.SupplyPrice, 0)
              - ISNULL(pp.UnitCost, 0)
              - ISNULL(pp.LogisticsCost, 0)
              - ISNULL(pp.ManagementCost, 0)
              - ISNULL(pp.WarehouseCost, 0)
            ) / pp.SupplyPrice) * 100
        WHEN pp.PromotionPrice > 0 THEN
            -- 위탁: 판매가 기준 마진율
            ((pp.PromotionPrice
              - ISNULL(pp.UnitCost, 0)
              - (pp.PromotionPrice * ISNULL(p.CommissionRate, 0) / 100)
              - ISNULL(pp.LogisticsCost, 0)
              - ISNULL(pp.ManagementCost, 0)
              - ISNULL(pp.WarehouseCost, 0)
            ) / pp.PromotionPrice) * 100
        ELSE NULL
    END AS CalculatedMarginRate,

    -- 목표
    pp.TargetSalesAmount,
    pp.TargetQuantity,
    pp.TargetProfit,
    pp.RequiredStockQty,

    -- 기타
    p.Notes AS PromotionNotes,
    pp.Notes AS ProductNotes,
    p.CreatedDate,
    p.UpdatedDate

FROM dbo.Promotion p
INNER JOIN dbo.PromotionProduct pp ON p.PromotionID = pp.PromotionProduct ID
INNER JOIN dbo.Brand b ON p.BrandID = b.BrandID
INNER JOIN dbo.Product prod ON pp.ProductID = prod.ProductID
WHERE p.ChannelType = N'OFFLINE';

-- ============================================
-- 3. 통합 행사 View (온/오프라인 통합)
-- ============================================
CREATE VIEW vw_PromotionAll AS
SELECT
    p.PromotionID,
    p.PromotionName,
    p.PromotionType,
    p.ChannelType,
    p.StartDate,
    p.EndDate,
    p.Status,

    -- 브랜드
    p.BrandID,
    b.BrandName,

    -- 채널
    p.ChannelNames,
    p.CommissionRate,

    -- 할인 분담
    p.DiscountOwner,
    p.OrioShare,
    p.ChannelShare,

    -- 오프라인 전용
    p.BundleCondition,

    -- 상품 정보
    pp.PromotionProductID,
    pp.ProductID,
    prod.ProductName,
    prod.ProductCode,

    -- 가격
    pp.RegularPrice,
    pp.SellingPrice,
    pp.PromotionPrice,
    pp.SupplyPrice,
    pp.UnitCost,

    -- 할인
    pp.DiscountRate,
    pp.CouponDiscountRate,

    -- 비용
    pp.SettlementType,
    pp.LogisticsCost,
    pp.ManagementCost,
    pp.WarehouseCost,

    -- 목표
    pp.TargetSalesAmount,
    pp.TargetQuantity,
    pp.TargetProfit,
    pp.RequiredStockQty,

    -- 마진 (채널별 계산 로직 적용)
    CASE
        WHEN p.ChannelType = N'ONLINE' THEN
            CASE
                WHEN pp.SettlementType = N'CONSIGNMENT' THEN
                    pp.PromotionPrice
                    - ISNULL(pp.UnitCost, 0)
                    - (pp.PromotionPrice * ISNULL(p.CommissionRate, 0) / 100)
                    - ISNULL(pp.LogisticsCost, 0)
                    - ISNULL(pp.ManagementCost, 0)
                    - ISNULL(pp.WarehouseCost, 0)
                ELSE
                    pp.PromotionPrice
                    - ISNULL(pp.UnitCost, 0)
                    - ISNULL(pp.LogisticsCost, 0)
                    - ISNULL(pp.ManagementCost, 0)
                    - ISNULL(pp.WarehouseCost, 0)
            END
        ELSE -- OFFLINE
            CASE
                WHEN pp.SettlementType = N'DIRECT' THEN
                    ISNULL(pp.SupplyPrice, 0)
                    - ISNULL(pp.UnitCost, 0)
                    - ISNULL(pp.LogisticsCost, 0)
                    - ISNULL(pp.ManagementCost, 0)
                    - ISNULL(pp.WarehouseCost, 0)
                ELSE
                    pp.PromotionPrice
                    - ISNULL(pp.UnitCost, 0)
                    - (pp.PromotionPrice * ISNULL(p.CommissionRate, 0) / 100)
                    - ISNULL(pp.LogisticsCost, 0)
                    - ISNULL(pp.ManagementCost, 0)
                    - ISNULL(pp.WarehouseCost, 0)
            END
    END AS CalculatedMarginAmount,

    -- 기타
    p.Notes AS PromotionNotes,
    pp.Notes AS ProductNotes,
    p.CreatedDate,
    p.UpdatedDate

FROM dbo.Promotion p
INNER JOIN dbo.PromotionProduct pp ON p.PromotionID = pp.PromotionID
INNER JOIN dbo.Brand b ON p.BrandID = b.BrandID
INNER JOIN dbo.Product prod ON pp.ProductID = prod.ProductID;

-- ============================================
-- 4. 행사 요약 View (대시보드용)
-- ============================================
CREATE VIEW vw_PromotionSummary AS
SELECT
    p.PromotionID,
    p.PromotionName,
    p.PromotionType,
    p.ChannelType,
    p.ChannelNames,
    p.StartDate,
    p.EndDate,
    p.Status,

    b.BrandName,

    -- 상품 개수
    COUNT(DISTINCT pp.ProductID) AS ProductCount,

    -- 목표 합계
    SUM(pp.TargetSalesAmount) AS TotalTargetSales,
    SUM(pp.TargetQuantity) AS TotalTargetQuantity,
    SUM(pp.TargetProfit) AS TotalTargetProfit,

    -- 평균 할인율
    AVG(pp.DiscountRate) AS AvgDiscountRate,

    -- 할인 분담
    p.DiscountOwner,
    p.OrioShare,
    p.ChannelShare

FROM dbo.Promotion p
INNER JOIN dbo.PromotionProduct pp ON p.PromotionID = pp.PromotionID
INNER JOIN dbo.Brand b ON p.BrandID = b.BrandID
GROUP BY
    p.PromotionID,
    p.PromotionName,
    p.PromotionType,
    p.ChannelType,
    p.ChannelNames,
    p.StartDate,
    p.EndDate,
    p.Status,
    b.BrandName,
    p.DiscountOwner,
    p.OrioShare,
    p.ChannelShare;
