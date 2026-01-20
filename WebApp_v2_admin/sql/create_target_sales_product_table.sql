-- ================================================
-- TargetSalesProduct (목표매출 - 상품별) 테이블 생성 스크립트
-- ================================================
-- 비행사(BASE): 상품별 월 목표매출 직접 입력
-- 행사(PROMOTION): Promotion 업로드 시 자동 생성
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
    PromotionID NVARCHAR(20) NULL,            -- PROMOTION일 때 필수
    PromotionProductID INT NULL,              -- PromotionProduct FK
    TargetAmount DECIMAL(18,2) NULL,                -- 목표 매출액
    TargetQuantity INT NULL,                        -- 목표 수량
    CreatedDate DATETIME DEFAULT GETDATE(),
    UpdatedDate DATETIME DEFAULT GETDATE(),

    -- FK 제약조건
    CONSTRAINT FK_TargetSales_Brand FOREIGN KEY (BrandID)
        REFERENCES [dbo].[Brand](BrandID),
    CONSTRAINT FK_TargetSales_Channel FOREIGN KEY (ChannelID)
        REFERENCES [dbo].[Channel](ChannelID),
    CONSTRAINT FK_TargetSales_Product FOREIGN KEY (ProductID)
        REFERENCES [dbo].[Product](ProductID),
    CONSTRAINT FK_TargetSales_Promotion FOREIGN KEY (PromotionID)
        REFERENCES [dbo].[Promotion](PromotionID),
    CONSTRAINT FK_TargetSales_PromotionProduct FOREIGN KEY (PromotionProductID)
        REFERENCES [dbo].[PromotionProduct](PromotionProductID),

    -- 유니크 제약조건
    -- Year + Month + Brand + Channel + Product + SalesType + PromotionID 조합 유니크
    CONSTRAINT UQ_TargetSalesProduct UNIQUE (
        [Year], [Month], BrandID, ChannelID, ProductID, SalesType, PromotionID
    ),

    -- CHECK 제약조건
    -- SalesType은 'BASE' 또는 'PROMOTION'만 허용
    CONSTRAINT CK_TargetSales_SalesType CHECK (
        SalesType IN ('BASE', 'PROMOTION')
    ),
    -- BASE면 PromotionID NULL, PROMOTION이면 PromotionID 필수
    CONSTRAINT CK_TargetSales_PromotionRequired CHECK (
        (SalesType = 'BASE' AND PromotionID IS NULL) OR
        (SalesType = 'PROMOTION' AND PromotionID IS NOT NULL)
    )
);
GO

-- 2. 인덱스 생성 (성능 최적화)
CREATE INDEX IX_TargetSales_YearMonth ON [dbo].[TargetSalesProduct]([Year], [Month]);
CREATE INDEX IX_TargetSales_Brand ON [dbo].[TargetSalesProduct](BrandID);
CREATE INDEX IX_TargetSales_Channel ON [dbo].[TargetSalesProduct](ChannelID);
CREATE INDEX IX_TargetSales_Product ON [dbo].[TargetSalesProduct](ProductID);
CREATE INDEX IX_TargetSales_SalesType ON [dbo].[TargetSalesProduct](SalesType);
CREATE INDEX IX_TargetSales_Promotion ON [dbo].[TargetSalesProduct](PromotionID)
    WHERE PromotionID IS NOT NULL;
GO

-- ================================================
-- 확인 쿼리
-- ================================================

-- 테이블 구조 확인
-- EXEC sp_help 'dbo.TargetSalesProduct';

-- 샘플 데이터 조회 (생성 후)
/*
SELECT
    t.TargetID, t.[Year], t.[Month],
    b.Name as BrandName, c.Name as ChannelName, p.Name as ProductName,
    t.SalesType, t.PromotionID, t.Amount, t.Quantity
FROM [dbo].[TargetSalesProduct] t
LEFT JOIN [dbo].[Brand] b ON t.BrandID = b.BrandID
LEFT JOIN [dbo].[Channel] c ON t.ChannelID = c.ChannelID
LEFT JOIN [dbo].[Product] p ON t.ProductID = p.ProductID
ORDER BY t.[Year], t.[Month], b.Name, c.Name;
*/

-- 집계 쿼리 예시
/*
-- 월별 총 목표매출
SELECT [Year], [Month], SUM(Amount) as TotalTarget
FROM [dbo].[TargetSalesProduct]
GROUP BY [Year], [Month]
ORDER BY [Year], [Month];

-- SalesType별 비교 (행사 vs 비행사)
SELECT [Year], [Month], SalesType, SUM(Amount) as TotalTarget
FROM [dbo].[TargetSalesProduct]
GROUP BY [Year], [Month], SalesType
ORDER BY [Year], [Month], SalesType;

-- 특정 행사의 목표매출
SELECT * FROM [dbo].[TargetSalesProduct]
WHERE PromotionID = 'SDPD260201';
*/