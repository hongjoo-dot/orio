-- ============================================================
-- Cafe24 공헌이익 산출 체크 쿼리 (방안 3: 하이브리드)
-- 조인 경로: D.ProductUniqueCode → Product.UniqueCode → ProductBox
-- 작성일: 2026-03-06
-- ============================================================


-- ============================================================
-- [공통 CTE] 상품별 단위 원가 선택 (1:N 처리)
--   UniqueCode 1개에 ProductBox가 여러 개일 수 있음
--   우선순위: ① QuantityInBox = 1 ② BoxID 오름차순 (가장 기본 단위 선택)
--   단, UnitCostKRW > 0 인 것만
-- ============================================================
-- ※ 아래 각 쿼리는 독립 실행 가능 (WITH 절 포함)


-- ============================================================
-- [1] 매핑 커버리지 확인
--     ProductUniqueCode → Product.UniqueCode → ProductBox 경로
--     원가 없는 상품이 얼마나 되는지 체크
-- ============================================================
WITH UnitCostPerProduct AS (
    SELECT
        p.UniqueCode,
        p.ProductID,
        pb.UnitCostKRW,
        ROW_NUMBER() OVER (
            PARTITION BY p.UniqueCode
            ORDER BY
                CASE WHEN pb.QuantityInBox = 1 THEN 0 ELSE 1 END,
                pb.BoxID
        ) AS rn
    FROM Product p
    JOIN ProductBox pb ON p.ProductID = pb.ProductID
    WHERE pb.UnitCostKRW IS NOT NULL AND pb.UnitCostKRW > 0
)
SELECT
    COUNT(*)                                                            AS 전체_상세건수,
    COUNT(d.ProductUniqueCode)                                         AS UniqueCode_존재,
    COUNT(ucp.UniqueCode)                                              AS ProductBox_매핑성공,
    COUNT(CASE WHEN ucp.UnitCostKRW > 0 THEN 1 END)                   AS UnitCost_있음,
    CAST(COUNT(ucp.UniqueCode) * 100.0
         / NULLIF(COUNT(d.ProductUniqueCode), 0) AS DECIMAL(5,1))     AS ProductBox_매핑률_PCT,
    CAST(COUNT(CASE WHEN ucp.UnitCostKRW > 0 THEN 1 END) * 100.0
         / NULLIF(COUNT(*), 0) AS DECIMAL(5,1))                       AS UnitCost_커버리지_PCT
FROM Cafe24OrdersDetail d
LEFT JOIN (SELECT * FROM UnitCostPerProduct WHERE rn = 1) ucp
    ON d.ProductUniqueCode = ucp.UniqueCode
WHERE d.order_status NOT IN ('cancelled', 'canceled', '취소완료');


-- ============================================================
-- [2] 원가 없는 상품 목록 확인
--     ProductBox 자체가 없거나 UnitCostKRW = 0/NULL 인 경우
-- ============================================================
WITH UnitCostPerProduct AS (
    SELECT
        p.UniqueCode,
        pb.UnitCostKRW,
        ROW_NUMBER() OVER (
            PARTITION BY p.UniqueCode
            ORDER BY
                CASE WHEN pb.QuantityInBox = 1 THEN 0 ELSE 1 END,
                pb.BoxID
        ) AS rn
    FROM Product p
    JOIN ProductBox pb ON p.ProductID = pb.ProductID
    WHERE pb.UnitCostKRW IS NOT NULL AND pb.UnitCostKRW > 0
)
SELECT TOP 30
    d.ProductUniqueCode,
    d.product_name,
    COUNT(*) AS 주문건수,
    SUM(d.quantity) AS 총수량
FROM Cafe24OrdersDetail d
LEFT JOIN (SELECT * FROM UnitCostPerProduct WHERE rn = 1) ucp
    ON d.ProductUniqueCode = ucp.UniqueCode
WHERE ucp.UniqueCode IS NULL
  AND d.ProductUniqueCode IS NOT NULL
  AND d.order_status NOT IN ('cancelled', 'canceled', '취소완료')
GROUP BY d.ProductUniqueCode, d.product_name
ORDER BY 주문건수 DESC;


-- ============================================================
-- [3] UniqueCode별 ProductBox 1:N 현황 확인
--     어떤 상품이 여러 ERPCode를 가지는지 파악
-- ============================================================
SELECT
    p.UniqueCode,
    p.Name,
    COUNT(pb.BoxID)                        AS ProductBox_개수,
    STRING_AGG(
        pb.ERPCode + '(qty:' + CAST(ISNULL(pb.QuantityInBox,0) AS VARCHAR)
        + ', 원가:' + ISNULL(CAST(pb.UnitCostKRW AS VARCHAR), 'NULL') + ')',
        ' / '
    )                                      AS ERPCode_목록
FROM Product p
JOIN ProductBox pb ON p.ProductID = pb.ProductID
GROUP BY p.UniqueCode, p.Name
HAVING COUNT(pb.BoxID) > 1
ORDER BY ProductBox_개수 DESC;


-- ============================================================
-- [4] 주문별 공헌이익 계산 (방안 3 메인 쿼리)
--   - 매출:      O.order_price_amount + O.shipping_fee (유료배송 수취분)
--   - 제품원가:  D.quantity × UnitCostKRW 합산
--   - 쿠폰할인:  O.coupon_discount_price
--   - 적립금:    O.points_spent_amount
--   - 배송실비:  건당 2,200원 고정
--   - 카드수수료: O.payment_amount × 3.3%
-- ============================================================
WITH UnitCostPerProduct AS (
    SELECT
        p.UniqueCode,
        pb.UnitCostKRW,
        ROW_NUMBER() OVER (
            PARTITION BY p.UniqueCode
            ORDER BY
                CASE WHEN pb.QuantityInBox = 1 THEN 0 ELSE 1 END,
                pb.BoxID
        ) AS rn
    FROM Product p
    JOIN ProductBox pb ON p.ProductID = pb.ProductID
    WHERE pb.UnitCostKRW IS NOT NULL AND pb.UnitCostKRW > 0
),
OrderUnitCost AS (
    SELECT
        d.Cafe24OrderID,
        SUM(d.quantity * ISNULL(ucp.UnitCostKRW, 0))   AS TotalUnitCost,
        COUNT(d.DetailID)                               AS ItemCount,
        COUNT(ucp.UniqueCode)                           AS MappedItemCount,
        CAST(
            COUNT(ucp.UniqueCode) * 100.0
            / NULLIF(COUNT(d.DetailID), 0)
        AS DECIMAL(5,1))                                AS CostMappingRate
    FROM Cafe24OrdersDetail d
    LEFT JOIN (SELECT * FROM UnitCostPerProduct WHERE rn = 1) ucp
        ON d.ProductUniqueCode = ucp.UniqueCode
    WHERE d.order_status NOT IN ('cancelled', 'canceled', '취소완료')
    GROUP BY d.Cafe24OrderID
)
SELECT
    o.order_id,
    CAST(o.order_date AS DATE)                              AS 주문일,
    o.order_status,
    o.member_id,

    -- 매출 구성
    o.order_price_amount                                    AS 상품매출,
    ISNULL(o.shipping_fee, 0)                               AS 배송비수취,
    o.order_price_amount + ISNULL(o.shipping_fee, 0)        AS 총매출,

    -- 비용 구성
    oc.TotalUnitCost                                        AS 제품원가,
    ISNULL(o.coupon_discount_price, 0)                      AS 쿠폰할인,
    ISNULL(o.points_spent_amount, 0)                        AS 적립금사용,
    2200                                                    AS 배송실비,
    CAST(o.payment_amount * 0.033 AS DECIMAL(18,0))         AS 카드수수료,

    -- 공헌이익 = 총매출 - 제품원가 - 쿠폰 - 적립금 - 배송실비 - 카드수수료
    CAST(
        (o.order_price_amount + ISNULL(o.shipping_fee, 0))
        - oc.TotalUnitCost
        - ISNULL(o.coupon_discount_price, 0)
        - ISNULL(o.points_spent_amount, 0)
        - 2200
        - (o.payment_amount * 0.033)
    AS DECIMAL(18,0))                                       AS 공헌이익,

    -- 공헌이익률 (총매출 대비)
    CAST(
        ((o.order_price_amount + ISNULL(o.shipping_fee, 0))
        - oc.TotalUnitCost
        - ISNULL(o.coupon_discount_price, 0)
        - ISNULL(o.points_spent_amount, 0)
        - 2200
        - (o.payment_amount * 0.033))
        * 100.0
        / NULLIF(o.order_price_amount + ISNULL(o.shipping_fee, 0), 0)
    AS DECIMAL(5,1))                                        AS 공헌이익률_PCT,

    -- 검증용
    o.payment_amount                                        AS 실결제금액,
    oc.CostMappingRate                                      AS 원가매핑률_PCT,
    oc.ItemCount                                            AS 품목수,
    oc.MappedItemCount                                      AS 원가매핑품목수

FROM Cafe24Orders o
JOIN OrderUnitCost oc ON o.Cafe24OrderID = oc.Cafe24OrderID
WHERE ISNULL(o.canceled, 0) = 0
  AND o.paid = 1
ORDER BY o.order_date DESC;


-- ============================================================
-- [5] SKU별 원가 기여 분석 (주문 내 상품별 breakdown)
--     방안 3 원칙: 매출 배분 없음, 원가 비중만 계산
--     D.payment_amount는 참고용으로만 출력
-- ============================================================
WITH UnitCostPerProduct AS (
    SELECT
        p.UniqueCode,
        pb.ERPCode,
        pb.UnitCostKRW,
        pb.QuantityInBox,
        ROW_NUMBER() OVER (
            PARTITION BY p.UniqueCode
            ORDER BY
                CASE WHEN pb.QuantityInBox = 1 THEN 0 ELSE 1 END,
                pb.BoxID
        ) AS rn
    FROM Product p
    JOIN ProductBox pb ON p.ProductID = pb.ProductID
    WHERE pb.UnitCostKRW IS NOT NULL AND pb.UnitCostKRW > 0
),
OrderTotalCost AS (
    SELECT
        d.Cafe24OrderID,
        SUM(d.quantity * ISNULL(ucp.UnitCostKRW, 0)) AS OrderTotalCost
    FROM Cafe24OrdersDetail d
    LEFT JOIN (SELECT * FROM UnitCostPerProduct WHERE rn = 1) ucp
        ON d.ProductUniqueCode = ucp.UniqueCode
    WHERE d.order_status NOT IN ('cancelled', 'canceled', '취소완료')
    GROUP BY d.Cafe24OrderID
)
SELECT
    o.order_id,
    CAST(o.order_date AS DATE)                          AS 주문일,
    d.ProductUniqueCode                                 AS 상품코드,
    d.product_name                                      AS 상품명,
    d.option_value                                      AS 옵션,
    ucp.ERPCode,
    ucp.QuantityInBox,
    d.quantity                                          AS 주문수량,
    ucp.UnitCostKRW                                     AS 단위원가,
    d.quantity * ISNULL(ucp.UnitCostKRW, 0)            AS 품목원가합계,
    d.payment_amount                                    AS 품목_실결제금액,    -- 참고용
    d.coupon_discount_price                             AS 품목_쿠폰할인,      -- 참고용

    -- 주문 내 원가 비중
    CAST(
        (d.quantity * ISNULL(ucp.UnitCostKRW, 0))
        * 100.0 / NULLIF(otc.OrderTotalCost, 0)
    AS DECIMAL(5,1))                                    AS 주문내_원가비중_PCT

FROM Cafe24OrdersDetail d
JOIN Cafe24Orders o         ON d.Cafe24OrderID = o.Cafe24OrderID
LEFT JOIN (SELECT * FROM UnitCostPerProduct WHERE rn = 1) ucp
    ON d.ProductUniqueCode = ucp.UniqueCode
LEFT JOIN OrderTotalCost otc ON d.Cafe24OrderID = otc.Cafe24OrderID
WHERE ISNULL(o.canceled, 0) = 0
  AND o.paid = 1
  AND d.order_status NOT IN ('cancelled', 'canceled', '취소완료')
ORDER BY o.order_date DESC, o.order_id, d.DetailID;


-- ============================================================
-- [6] 월별 공헌이익 집계
-- ============================================================
WITH UnitCostPerProduct AS (
    SELECT
        p.UniqueCode,
        pb.UnitCostKRW,
        ROW_NUMBER() OVER (
            PARTITION BY p.UniqueCode
            ORDER BY
                CASE WHEN pb.QuantityInBox = 1 THEN 0 ELSE 1 END,
                pb.BoxID
        ) AS rn
    FROM Product p
    JOIN ProductBox pb ON p.ProductID = pb.ProductID
    WHERE pb.UnitCostKRW IS NOT NULL AND pb.UnitCostKRW > 0
),
OrderUnitCost AS (
    SELECT
        d.Cafe24OrderID,
        SUM(d.quantity * ISNULL(ucp.UnitCostKRW, 0))   AS TotalUnitCost,
        COUNT(d.DetailID)                               AS ItemCount,
        COUNT(ucp.UniqueCode)                           AS MappedCount
    FROM Cafe24OrdersDetail d
    LEFT JOIN (SELECT * FROM UnitCostPerProduct WHERE rn = 1) ucp
        ON d.ProductUniqueCode = ucp.UniqueCode
    WHERE d.order_status NOT IN ('cancelled', 'canceled', '취소완료')
    GROUP BY d.Cafe24OrderID
)
SELECT
    FORMAT(o.order_date, 'yyyy-MM')                                     AS 월,
    COUNT(DISTINCT o.order_id)                                          AS 주문수,
    SUM(o.order_price_amount + ISNULL(o.shipping_fee, 0))               AS 총매출,
    SUM(oc.TotalUnitCost)                                               AS 총원가,
    SUM(ISNULL(o.coupon_discount_price, 0))                             AS 총쿠폰할인,
    SUM(ISNULL(o.points_spent_amount, 0))                               AS 총적립금사용,
    COUNT(DISTINCT o.order_id) * 2200                                   AS 총배송실비,
    CAST(SUM(o.payment_amount * 0.033) AS DECIMAL(18,0))                AS 총카드수수료,
    CAST(SUM(
        (o.order_price_amount + ISNULL(o.shipping_fee, 0))
        - oc.TotalUnitCost
        - ISNULL(o.coupon_discount_price, 0)
        - ISNULL(o.points_spent_amount, 0)
        - 2200
        - (o.payment_amount * 0.033)
    ) AS DECIMAL(18,0))                                                 AS 총공헌이익,
    CAST(
        SUM(
            (o.order_price_amount + ISNULL(o.shipping_fee, 0))
            - oc.TotalUnitCost
            - ISNULL(o.coupon_discount_price, 0)
            - ISNULL(o.points_spent_amount, 0)
            - 2200
            - (o.payment_amount * 0.033)
        )
        * 100.0
        / NULLIF(SUM(o.order_price_amount + ISNULL(o.shipping_fee, 0)), 0)
    AS DECIMAL(5,1))                                                    AS 공헌이익률_PCT

FROM Cafe24Orders o
JOIN OrderUnitCost oc ON o.Cafe24OrderID = oc.Cafe24OrderID
WHERE ISNULL(o.canceled, 0) = 0
  AND o.paid = 1
  -- 원가 완전 매핑 주문만 필터 (선택적 적용)
  -- AND oc.ItemCount = oc.MappedCount
GROUP BY FORMAT(o.order_date, 'yyyy-MM')
ORDER BY 월 DESC;