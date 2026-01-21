-- ================================================
-- ExpectedSalesProduct (예상매출 - 상품별) 테이블 생성 스크립트
-- ================================================
-- 비행사(BASE): 상품별 월 예상매출 직접 입력
-- 행사(PROMOTION): Promotion 업로드 시 자동 생성
-- ================================================

-- 1. 테이블 생성
CREATE TABLE [dbo].[ExpectedSalesProduct] (
    ExpectedID INT IDENTITY(1,1) PRIMARY KEY,
    [Year] INT NOT NULL,
    [Month] INT NOT NULL,
    BrandID INT NOT NULL,
    ChannelID INT NOT NULL,
    ProductID INT NOT NULL,
    SalesType NVARCHAR(20) NOT NULL,          -- 'BASE' / 'PROMOTION'
    PromotionID NVARCHAR(20) NULL,            -- PROMOTION일 때 필수
    PromotionProductID INT NULL,              -- PromotionProduct FK
    ExpectedAmount DECIMAL(18,2) NULL,        -- 예상 매출액
    ExpectedQuantity INT NULL,                -- 예상 수량
    CreatedDate DATETIME DEFAULT GETDATE(),
    UpdatedDate DATETIME DEFAULT GETDATE(),

    -- FK 제약조건
    CONSTRAINT FK_ExpectedSales_Brand FOREIGN KEY (BrandID)
        REFERENCES [dbo].[Brand](BrandID),
    CONSTRAINT FK_ExpectedSales_Channel FOREIGN KEY (ChannelID)
        REFERENCES [dbo].[Channel](ChannelID),
    CONSTRAINT FK_ExpectedSales_Product FOREIGN KEY (ProductID)
        REFERENCES [dbo].[Product](ProductID),
    CONSTRAINT FK_ExpectedSales_Promotion FOREIGN KEY (PromotionID)
        REFERENCES [dbo].[Promotion](PromotionID),
    CONSTRAINT FK_ExpectedSales_PromotionProduct FOREIGN KEY (PromotionProductID)
        REFERENCES [dbo].[PromotionProduct](PromotionProductID),

    -- 유니크 제약조건
    -- Year + Month + Brand + Channel + Product + SalesType + PromotionID 조합 유니크
    CONSTRAINT UQ_ExpectedSalesProduct UNIQUE (
        [Year], [Month], BrandID, ChannelID, ProductID, SalesType, PromotionID
    ),

    -- CHECK 제약조건
    -- SalesType은 'BASE' 또는 'PROMOTION'만 허용
    CONSTRAINT CK_ExpectedSales_SalesType CHECK (
        SalesType IN ('BASE', 'PROMOTION')
    ),
    -- BASE면 PromotionID NULL, PROMOTION이면 PromotionID 필수
    CONSTRAINT CK_ExpectedSales_PromotionRequired CHECK (
        (SalesType = 'BASE' AND PromotionID IS NULL) OR
        (SalesType = 'PROMOTION' AND PromotionID IS NOT NULL)
    )
);
GO

-- 2. 인덱스 생성 (성능 최적화)
CREATE INDEX IX_ExpectedSales_YearMonth ON [dbo].[ExpectedSalesProduct]([Year], [Month]);
CREATE INDEX IX_ExpectedSales_Brand ON [dbo].[ExpectedSalesProduct](BrandID);
CREATE INDEX IX_ExpectedSales_Channel ON [dbo].[ExpectedSalesProduct](ChannelID);
CREATE INDEX IX_ExpectedSales_Product ON [dbo].[ExpectedSalesProduct](ProductID);
CREATE INDEX IX_ExpectedSales_SalesType ON [dbo].[ExpectedSalesProduct](SalesType);
CREATE INDEX IX_ExpectedSales_Promotion ON [dbo].[ExpectedSalesProduct](PromotionID)
    WHERE PromotionID IS NOT NULL;
GO