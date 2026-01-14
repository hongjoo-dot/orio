-- ============================================
-- vw_PendingOrders: 미출고 주문 View
-- Power BI 물류센터 대시보드용
-- ============================================

CREATE OR ALTER VIEW dbo.vw_PendingOrders AS

-- Cafe24 미출고 주문
SELECT
    'Cafe24' AS SourceChannel,
    o.order_id AS OrderID,
    d.order_item_code AS OrderItemCode,
    o.order_date AS OrderDate,
    o.payment_date AS PaymentDate,
    o.order_status AS OrderStatus,
    o.shipping_status AS ShippingStatus,
    o.billing_name AS CustomerName,
    d.product_name AS ProductName,
    d.option_value AS OptionValue,
    d.custom_product_code AS ProductCode,
    d.quantity AS Quantity,
    d.product_price AS UnitPrice,
    d.payment_amount AS PaymentAmount,
    d.ProductID,
    p.BrandID,
    b.Name AS BrandName,
    o.CollectedDate
FROM dbo.Cafe24Orders o
INNER JOIN dbo.Cafe24OrdersDetail d ON o.order_id = d.order_id
LEFT JOIN dbo.Product p ON d.ProductID = p.ProductID
LEFT JOIN dbo.Brand b ON p.BrandID = b.BrandID
WHERE o.shipped_date IS NULL
  AND o.canceled = 0
  AND o.order_date >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE))

UNION ALL

-- Sabangnet 미출고 주문
SELECT
    'Sabangnet' AS SourceChannel,
    o.ORDER_ID AS OrderID,
    CAST(d.IDX AS NVARCHAR(100)) AS OrderItemCode,
    o.ORDER_DATE AS OrderDate,
    NULL AS PaymentDate,
    o.ORDER_STATUS AS OrderStatus,
    NULL AS ShippingStatus,
    o.USER_NAME AS CustomerName,
    d.PRODUCT_NAME AS ProductName,
    NULL AS OptionValue,
    d.PRODUCT_ID AS ProductCode,
    d.SALE_CNT AS Quantity,
    o.PAY_COST AS UnitPrice,
    o.PAY_COST AS PaymentAmount,
    d.ProductID,
    p.BrandID,
    b.Name AS BrandName,
    o.CollectedDate
FROM dbo.SabangnetOrders o
INNER JOIN dbo.SabangnetOrdersDetail d ON o.IDX = d.IDX
LEFT JOIN dbo.Product p ON d.ProductID = p.ProductID
LEFT JOIN dbo.Brand b ON p.BrandID = b.BrandID
WHERE o.DELIVERY_CONFIRM_DATE IS NULL
  AND o.ORDER_DATE >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE));

GO

-- ============================================
-- vw_PendingOrdersSummary: 미출고 주문 요약 View
-- 물류센터 간단 현황 조회용
-- ============================================

CREATE OR ALTER VIEW dbo.vw_PendingOrdersSummary AS
SELECT
    SourceChannel,
    CAST(OrderDate AS DATE) AS OrderDate,
    BrandName,
    COUNT(DISTINCT OrderID) AS OrderCount,
    SUM(Quantity) AS TotalQuantity,
    SUM(PaymentAmount) AS TotalAmount,
    MAX(CollectedDate) AS LastCollectedDate
FROM dbo.vw_PendingOrders
GROUP BY
    SourceChannel,
    CAST(OrderDate AS DATE),
    BrandName;

GO
