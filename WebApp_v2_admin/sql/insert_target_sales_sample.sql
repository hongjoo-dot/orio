-- ================================================
-- TargetSalesProduct 샘플 데이터 INSERT
-- ================================================
-- 실행 전 Brand, Channel, Product 테이블에 해당 ID가 존재해야 합니다.
-- ================================================

-- 기존 샘플 데이터 삭제 (필요시)
-- DELETE FROM [dbo].[TargetSalesProduct] WHERE Notes LIKE '%샘플%';

-- 2026년 1월 목표매출 샘플
INSERT INTO [dbo].[TargetSalesProduct]
    ([Year], [Month], BrandID, ChannelID, ProductID, SalesType, TargetAmount, TargetQuantity, Notes)
VALUES
    -- 스크럽대디(BrandID=1), 쿠팡(ChannelID=1), 상품1(ProductID=1)
    (2026, 1, 1, 1, 1, 'BASE', 50000000, 2500, '2026년 1월 샘플'),
    (2026, 1, 1, 1, 1, 'PROMOTION', 30000000, 1500, '2026년 1월 샘플'),

    -- 스크럽대디(BrandID=1), 쿠팡(ChannelID=1), 상품2(ProductID=2)
    (2026, 1, 1, 1, 2, 'BASE', 40000000, 2000, '2026년 1월 샘플'),
    (2026, 1, 1, 1, 2, 'PROMOTION', 25000000, 1200, '2026년 1월 샘플'),

    -- 스크럽대디(BrandID=1), 네이버(ChannelID=2), 상품1(ProductID=1)
    (2026, 1, 1, 2, 1, 'BASE', 35000000, 1800, '2026년 1월 샘플'),
    (2026, 1, 1, 2, 1, 'PROMOTION', 20000000, 1000, '2026년 1월 샘플');

-- 2026년 2월 목표매출 샘플
INSERT INTO [dbo].[TargetSalesProduct]
    ([Year], [Month], BrandID, ChannelID, ProductID, SalesType, TargetAmount, TargetQuantity, Notes)
VALUES
    (2026, 2, 1, 1, 1, 'BASE', 55000000, 2700, '2026년 2월 샘플'),
    (2026, 2, 1, 1, 1, 'PROMOTION', 32000000, 1600, '2026년 2월 샘플'),
    (2026, 2, 1, 1, 2, 'BASE', 42000000, 2100, '2026년 2월 샘플'),
    (2026, 2, 1, 2, 1, 'BASE', 38000000, 1900, '2026년 2월 샘플');

-- 결과 확인
SELECT
    t.TargetID,
    t.[Year],
    t.[Month],
    b.Name AS BrandName,
    c.Name AS ChannelName,
    p.Name AS ProductName,
    t.SalesType,
    t.TargetAmount,
    t.TargetQuantity,
    t.Notes
FROM [dbo].[TargetSalesProduct] t
LEFT JOIN [dbo].[Brand] b ON t.BrandID = b.BrandID
LEFT JOIN [dbo].[Channel] c ON t.ChannelID = c.ChannelID
LEFT JOIN [dbo].[Product] p ON t.ProductID = p.ProductID
WHERE t.Notes LIKE '%샘플%'
ORDER BY t.[Year], t.[Month], t.BrandID, t.ChannelID, t.ProductID, t.SalesType;
