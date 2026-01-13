-- ============================================
-- 행사 관리 시스템 - Phase 1
-- 온/오프라인 통합 구조
-- ============================================

-- ============================================
-- 1. Promotion (행사 마스터 테이블)
-- ============================================
CREATE TABLE dbo.Promotion (
    PromotionID int IDENTITY(1,1) PRIMARY KEY,
    PromotionName nvarchar(200) NOT NULL,
    PromotionType nvarchar(50) NULL,              -- PRICE_DISCOUNT(판매가할인) / COUPON / WHOLESALE_DISCOUNT(원매가) / BUNDLE_DISCOUNT(에누리) / SPECIAL_PRODUCT(기획)
    StartDate date NOT NULL,
    EndDate date NOT NULL,
    Status nvarchar(20) DEFAULT 'SCHEDULED' NULL, -- SCHEDULED / ACTIVE / COMPLETED / CANCELLED

    -- 기본 정보
    BrandID int NOT NULL,
    ChannelID int NOT NULL,                       -- Phase 1에서는 미사용 (FK 없음)
    ChannelType nvarchar(20) NULL,                -- ONLINE / OFFLINE / BOTH
    ChannelNames nvarchar(500) NULL,              -- "쿠팡, 네이버스토어" or "이마트, 홈플러스"
    CommissionRate decimal(5,2) NULL,             -- 채널 수수료율 (%)

    -- 할인 분담 구조
    DiscountOwner nvarchar(20) NULL,              -- ORIO / CHANNEL / BOTH
    OrioShare decimal(5,2) NULL,                  -- 오리오 분담률 (%)
    ChannelShare decimal(5,2) NULL,               -- 판매채널 분담률 (%)

    -- 오프라인 전용
    BundleCondition nvarchar(200) NULL,           -- "3개 구매시 20% 할인", "2+1 증정"

    -- 목표 (행사 전체 합계)
    TargetSalesAmount decimal(18,2) NULL,         -- 매출 목표
    TargetQuantity int NULL,                      -- 수량 목표
    TargetProfit decimal(18,2) NULL,              -- 목표 순이익

    -- 상태
    IsActive bit DEFAULT 1 NOT NULL,

    -- 기타
    Notes nvarchar(MAX) NULL,
    CreatedDate datetime DEFAULT GETDATE(),
    UpdatedDate datetime DEFAULT GETDATE(),

    CONSTRAINT FK_Promotion_Brand
        FOREIGN KEY (BrandID) REFERENCES dbo.Brand(BrandID)
);

-- ============================================
-- 2. PromotionProduct (행사 상품 테이블)
-- ============================================
CREATE TABLE dbo.PromotionProduct (
    PromotionProductID int IDENTITY(1,1) PRIMARY KEY,
    PromotionID int NOT NULL,
    ProductID int NOT NULL,

    -- ========================================
    -- 가격 구조
    -- ========================================
    RegularPrice decimal(18,2) NULL,              -- 정가
    SellingPrice decimal(18,2) NULL,              -- 상시판매가
    PromotionPrice decimal(18,2) NULL,            -- 행사가
    SupplyPrice decimal(18,2) NULL,               -- 공급가 (정산가, 원매가 할인 포함)
    DiscountRate decimal(5,2) NULL,               -- 판매가 할인율 (직접 입력)
    CouponDiscountRate decimal(5,2) NULL,         -- 쿠폰 할인율 (직접 입력)

    -- ========================================
    -- 비용 구조
    -- ========================================
    UnitCost decimal(18,2) NULL,                  -- 상품원가
    SettlementType nvarchar(20) NULL,             -- DIRECT / CONSIGNMENT
    LogisticsCost decimal(18,2) NULL,             -- 단위당 물류비
    ManagementCost decimal(18,2) NULL,            -- 단위당 관리비
    WarehouseCost decimal(18,2) NULL,             -- 단위당 창고비

    -- 마진 (계산으로 채워질 예정)
    MarginRate decimal(5,2) NULL,                 -- 마진율 (%)
    MarginAmount decimal(18,2) NULL,              -- 단위당 마진액

    -- ========================================
    -- 목표 (상품별)
    -- ========================================
    TargetSalesAmount decimal(18,2) NULL,         -- 매출 목표
    TargetQuantity int NULL,                      -- 수량 목표
    TargetProfit decimal(18,2) NULL,              -- 목표 순이익
    RequiredStockQty int NULL,                    -- 필요 재고 수량

    -- ========================================
    -- 기타
    -- ========================================
    Notes nvarchar(MAX) NULL,
    IsActive bit DEFAULT 1 NOT NULL,
    CreatedDate datetime DEFAULT GETDATE(),
    UpdatedDate datetime DEFAULT GETDATE(),

    CONSTRAINT FK_PromotionProduct_Promotion
        FOREIGN KEY (PromotionID) REFERENCES dbo.Promotion(PromotionID),
    CONSTRAINT FK_PromotionProduct_Product
        FOREIGN KEY (ProductID) REFERENCES dbo.Product(ProductID),
    CONSTRAINT UQ_PromotionProduct
        UNIQUE (PromotionID, ProductID)
);

-- ============================================
-- 3. 인덱스
-- ============================================
CREATE INDEX IX_Promotion_Brand ON dbo.Promotion(BrandID);
CREATE INDEX IX_Promotion_Date ON dbo.Promotion(StartDate, EndDate);
CREATE INDEX IX_Promotion_Status ON dbo.Promotion(Status);
CREATE INDEX IX_Promotion_Type ON dbo.Promotion(PromotionType);

CREATE INDEX IX_PromotionProduct_Promotion ON dbo.PromotionProduct(PromotionID);
CREATE INDEX IX_PromotionProduct_Product ON dbo.PromotionProduct(ProductID);

-- ============================================
-- 4. 샘플 데이터
-- ============================================

-- 온라인 행사: 쿠팡 판매가 할인 + 쿠폰
INSERT INTO dbo.Promotion (
    PromotionName, PromotionType, StartDate, EndDate,
    BrandID, ChannelID, ChannelType, ChannelNames,
    CommissionRate,
    DiscountOwner, OrioShare, ChannelShare,
    TargetSalesAmount, TargetQuantity,
    Status
)
VALUES (
    '쿠팡 로켓배송 특가', 'PRICE_DISCOUNT', '2026-02-01', '2026-02-07',
    1, 0, 'ONLINE', '쿠팡',
    15.00,
    'BOTH', 60.00, 40.00,
    10000000.00, 5000,
    'SCHEDULED'
);

INSERT INTO dbo.PromotionProduct (
    PromotionID, ProductID,
    RegularPrice, SellingPrice, PromotionPrice, SupplyPrice, UnitCost,
    DiscountRate, CouponDiscountRate,
    SettlementType, LogisticsCost,
    TargetSalesAmount, TargetQuantity
)
VALUES (
    1, 1,
    12000.00, 10000.00, 8500.00, 7000.00, 5000.00,
    15.00, 5.00,
    'CONSIGNMENT', 500.00,
    42500000.00, 5000
);

-- 오프라인 행사 1: 원매가 할인
INSERT INTO dbo.Promotion (
    PromotionName, PromotionType, StartDate, EndDate,
    BrandID, ChannelID, ChannelType, ChannelNames,
    DiscountOwner, OrioShare,
    TargetSalesAmount, TargetQuantity,
    Status
)
VALUES (
    '롯데마트 원매가 할인', 'WHOLESALE_DISCOUNT', '2026-02-15', '2026-02-21',
    1, 0, 'OFFLINE', '롯데마트',
    'ORIO', 100.00,
    3000000.00, 2000,
    'SCHEDULED'
);

INSERT INTO dbo.PromotionProduct (
    PromotionID, ProductID,
    RegularPrice, SellingPrice, PromotionPrice, SupplyPrice, UnitCost,
    SettlementType,
    TargetSalesAmount, TargetQuantity
)
VALUES (
    2, 1,
    12000.00, 10000.00, 10000.00, 6000.00, 5000.00,
    'DIRECT',
    20000000.00, 2000
);

-- 오프라인 행사 2: 에누리 (묶음 할인)
INSERT INTO dbo.Promotion (
    PromotionName, PromotionType, StartDate, EndDate,
    BrandID, ChannelID, ChannelType, ChannelNames,
    DiscountOwner, OrioShare,
    BundleCondition,
    TargetSalesAmount, TargetQuantity,
    Status
)
VALUES (
    '이마트 3개 구매 할인', 'BUNDLE_DISCOUNT', '2026-02-01', '2026-02-28',
    1, 0, 'OFFLINE', '이마트, 홈플러스',
    'ORIO', 100.00,
    '3개 구매시 20% 할인',
    5000000.00, 3000,
    'SCHEDULED'
);

INSERT INTO dbo.PromotionProduct (
    PromotionID, ProductID,
    RegularPrice, SellingPrice, PromotionPrice, SupplyPrice, UnitCost,
    DiscountRate,
    SettlementType,
    TargetSalesAmount, TargetQuantity
)
VALUES (
    3, 1,
    12000.00, 10000.00, 8000.00, 7000.00, 5000.00,
    20.00,
    'DIRECT',
    24000000.00, 3000
);
