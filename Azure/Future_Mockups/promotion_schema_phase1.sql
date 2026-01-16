-- ============================================
-- 행사 관리 시스템 - Phase 1
-- 온/오프라인 통합 구조
-- ============================================

-- ============================================
-- 1. Promotion (행사 마스터 테이블)
-- ============================================
CREATE TABLE dbo.Promotion (
    PromotionID nvarchar(20) PRIMARY KEY,         -- 조합코드: 브랜드(2)+유형(2)+년월(4)+순번(2) ex) SDPD260201
    PromotionName nvarchar(200) NOT NULL,
    PromotionType nvarchar(50) NULL,
-- ============================================
-- 	온라인
-- 	'ONLINE_PRICE_DISCOUNT'      	-- PD: 판매가할인
-- 	'ONLINE_COUPON'              	-- CP: 쿠폰
-- 	'ONLINE_PRICE_COUPON'        	-- PC: 판매가+쿠폰
-- 	'ONLINE_POST_SETTLEMENT'     	-- PS: 정산후보정
-- 	오프라인
-- 	'OFFLINE_WHOLESALE_DISCOUNT' 	-- WD: 원매가할인
-- 	'OFFLINE_SPECIAL_PRODUCT'    	-- SP: 기획상품
-- 	'OFFLINE_BUNDLE_DISCOUNT'    	-- BD: 에누리(묶음할인)
-- ============================================   
    StartDate date NOT NULL,
    EndDate date NOT NULL,
    Status nvarchar(20) DEFAULT 'SCHEDULED' NULL, -- SCHEDULED / ACTIVE / COMPLETED / CANCELLED

    -- 기본 정보
    BrandID int NOT NULL,
    ChannelID int NOT NULL,                       -- Phase 1에서는 미사용 (FK 없음)
    ChannelName nvarchar(500) NULL,              -- "쿠팡, 네이버스토어" or "이마트, 홈플러스"
    CommissionRate decimal(5,2) NULL,             -- 채널 수수료율 (%)

    -- 할인 분담 구조
    DiscountOwner nvarchar(20) NULL,              -- COMPANY / CHANNEL / BOTH
    CompanyShare decimal(5,2) NULL,               -- 회사 분담률 (%)
    ChannelShare decimal(5,2) NULL,               -- 판매채널 분담률 (%)

    -- 목표 (행사 전체 합계)
    TargetSalesAmount decimal(18,2) NULL,         -- 매출 목표
    TargetQuantity int NULL,                      -- 수량 목표

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
    PromotionID nvarchar(20) NOT NULL,
    ProductID int NOT NULL,
    Uniquecode int NOT NULL,

    -- ========================================
    -- 가격 구조
    -- ========================================
    SellingPrice decimal(18,2) NULL,              -- 상시판매가
    PromotionPrice decimal(18,2) NULL,            -- 행사가 (판매가할인)
    SupplyPrice decimal(18,2) NULL,               -- 공급가 (원매가할인)
    CouponDiscountRate decimal(5,2) NULL,         -- 쿠폰 할인율 (직접 입력)

    -- ========================================
    -- 비용 구조
    -- ========================================
    UnitCost decimal(18,2) NULL,                  -- 상품원가
    LogisticsCost decimal(18,2) NULL,             -- 단위당 물류비
    ManagementCost decimal(18,2) NULL,            -- 단위당 관리비
    WarehouseCost decimal(18,2) NULL,             -- 단위당 창고비
    EDICost decimal(18,2) NULL,             	  -- 단위당 EDI비용
    MisCost decimal(18,2) NULL,             	  -- 단위당 잡손실

    -- ========================================
    -- 목표 (상품별)
    -- ========================================
    TargetSalesAmount decimal(18,2) NULL,         -- 매출 목표
    TargetQuantity int NULL,                      -- 수량 목표

    -- ========================================
    -- 기타
    -- ========================================
    Notes nvarchar(MAX) NULL,
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
