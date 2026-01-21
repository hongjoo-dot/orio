-- ================================================
-- TargetSalesProduct (목표매출 - 상품별) 테이블 생성 스크립트
-- ================================================
-- Promotion과 독립적으로 채널/브랜드별 월 목표 매출 관리
-- ================================================

-- 1. 테이블 생성
CREATE TABLE [dbo].[TargetSalesProduct] (
    TargetID INT IDENTITY(1,1) PRIMARY KEY,
    [Year] INT NOT NULL,
    [Month] INT NOT NULL,
    BrandID INT NOT NULL,
    ChannelID INT NOT NULL,
    ProductID INT NOT NULL,
    SalesType NVARCHAR(20) NOT NULL,          -- 'BASE' / 'PROMOTION'
    TargetAmount DECIMAL(18,2) NULL,        -- 목표 매출액
    TargetQuantity INT NULL,                -- 목표 수량
    Notes NVARCHAR(500) NULL,               -- 비고
    CreatedDate DATETIME DEFAULT GETDATE(),
    UpdatedDate DATETIME DEFAULT GETDATE(),

    -- FK 제약조건
    CONSTRAINT FK_TargetSales_Brand FOREIGN KEY (BrandID)
        REFERENCES [dbo].[Brand](BrandID),
    CONSTRAINT FK_TargetSales_Channel FOREIGN KEY (ChannelID)
        REFERENCES [dbo].[Channel](ChannelID),
    CONSTRAINT FK_TargetSales_Product FOREIGN KEY (ProductID)
        REFERENCES [dbo].[Product](ProductID),

    -- 유니크 제약조건
    -- Year + Month + Brand + Channel + Product + SalesType 조합 유니크
    CONSTRAINT UQ_TargetSalesProduct UNIQUE (
        [Year], [Month], BrandID, ChannelID, ProductID, SalesType
    ),

    -- CHECK 제약조건
    CONSTRAINT CK_TargetSales_SalesType CHECK (
        SalesType IN ('BASE', 'PROMOTION')
    )
);
GO

-- 2. 인덱스 생성 (성능 최적화)
CREATE INDEX IX_TargetSales_YearMonth ON [dbo].[TargetSalesProduct]([Year], [Month]);
CREATE INDEX IX_TargetSales_Brand ON [dbo].[TargetSalesProduct](BrandID);
CREATE INDEX IX_TargetSales_Channel ON [dbo].[TargetSalesProduct](ChannelID);
CREATE INDEX IX_TargetSales_Product ON [dbo].[TargetSalesProduct](ProductID);
CREATE INDEX IX_TargetSales_SalesType ON [dbo].[TargetSalesProduct](SalesType);
GO
