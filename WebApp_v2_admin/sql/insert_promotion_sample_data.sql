-- =====================================================
-- Promotion / PromotionProduct 예시 데이터
-- 행사 2건, 각 행사별 상품 3건 (총 6건)
--
-- 주의: BrandID, ChannelID는 실제 DB의 Brand, Channel 테이블에
--       존재하는 값으로 변경해야 합니다. (FK 제약)
--       PromotionType도 PromotionType 테이블의 DisplayName과 일치해야 합니다.
-- =====================================================

-- =====================================================
-- 1. Promotion 데이터 (2건)
-- PromotionID 형식: BrandCode(2) + TypeCode(2) + YYMM(4) + Seq(2)
-- =====================================================

INSERT INTO [dbo].[Promotion]
    (PromotionID, PromotionName, PromotionType,
     StartDate, StartTime, EndDate, EndTime,
     Status, BrandID, BrandName, ChannelID, ChannelName,
     CommissionRate, DiscountOwner, CompanyShare, ChannelShare,
     ExpectedSalesAmount, ExpectedQuantity, Notes)
VALUES
-- 행사 1: 오리오 + 쿠팡 타임딜
(N'OREN2601', N'1월 쿠팡 타임딜', N'타임딜',
 '2026-01-15', '10:00:00', '2026-01-17', '23:59:00',
 N'ACTIVE', 1, N'오리오', 1, N'쿠팡',
 15.00, N'COMPANY', NULL, NULL,
 5000000.00, 500, N'1월 타임딜 프로모션'),

-- 행사 2: 오리오 + 네이버 할인쿠폰
(N'OREN2602', N'1월 네이버 할인쿠폰', N'할인쿠폰',
 '2026-01-20', '00:00:00', '2026-01-31', '23:59:00',
 N'SCHEDULED', 1, N'오리오', 2, N'네이버',
 12.50, N'BOTH', 60.00, 40.00,
 8000000.00, 1000, N'1월 네이버 쿠폰 행사');

-- =====================================================
-- 2. PromotionProduct 데이터 (6건: 행사별 3개 상품)
-- PromotionProductID는 IDENTITY이므로 자동 생성
-- =====================================================

INSERT INTO [dbo].[PromotionProduct]
    (PromotionID, UniqueCode, ProductName,
     SellingPrice, PromotionPrice, SupplyPrice,
     CouponDiscountRate, UnitCost, LogisticsCost,
     ManagementCost, WarehouseCost, EDICost, MisCost,
     ExpectedSalesAmount, ExpectedQuantity, Notes)
VALUES
-- 행사 1 (OREN2601) 상품 3건
(N'OREN2601', N'P001', N'오리오 초코 쿠키 100g',
 5900.00, 4900.00, 3500.00,
 NULL, 2000.00, 300.00,
 150.00, 100.00, 50.00, 50.00,
 2450000.00, 250, N'인기상품'),

(N'OREN2601', N'P002', N'오리오 딸기 쿠키 100g',
 5900.00, 4900.00, 3500.00,
 NULL, 2100.00, 300.00,
 150.00, 100.00, 50.00, 50.00,
 1470000.00, 150, NULL),

(N'OREN2601', N'P003', N'오리오 바닐라 쿠키 100g',
 5500.00, 4500.00, 3200.00,
 NULL, 1900.00, 300.00,
 150.00, 100.00, 50.00, 50.00,
 450000.00, 100, NULL),

-- 행사 2 (OREN2602) 상품 3건
(N'OREN2602', N'P001', N'오리오 초코 쿠키 100g',
 5900.00, 5300.00, 3500.00,
 10.00, 2000.00, 300.00,
 150.00, 100.00, 50.00, 50.00,
 2650000.00, 500, N'10% 쿠폰 적용'),

(N'OREN2602', N'P004', N'오리오 더블스터프 150g',
 8900.00, 8000.00, 5500.00,
 10.00, 3200.00, 400.00,
 200.00, 150.00, 80.00, 70.00,
 2400000.00, 300, N'10% 쿠폰 적용'),

(N'OREN2602', N'P005', N'오리오 씬즈 초코 84g',
 4500.00, 4000.00, 2800.00,
 10.00, 1500.00, 250.00,
 120.00, 80.00, 40.00, 40.00,
 800000.00, 200, NULL);

PRINT N'Promotion 예시 데이터 2건, PromotionProduct 예시 데이터 6건 삽입 완료';
