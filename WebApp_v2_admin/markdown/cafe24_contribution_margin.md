# Cafe24 공헌이익 산출 시스템

## 개요

자사몰(Cafe24) 주문 데이터 기반 공헌이익 자동 산출.
주문 단위로 정확한 공헌이익을 계산하고, SKU별 원가 비중을 분석한다.

SQL 파일: `sql/cafe24_contribution_margin_check.sql`

## 공헌이익 공식

```
공헌이익 = 총매출 - 제품원가 - 쿠폰할인 - 적립금사용 - 배송실비 - 카드수수료
```

| 항목 | 산출 방식 | 비고 |
|------|-----------|------|
| 총매출 | `O.order_price_amount + O.shipping_fee` | 유료배송 시 배송비 수취(3,000원) 포함 |
| 제품원가 | `SUM(D.quantity × ProductBox.UnitCostKRW)` | 주문 내 전 품목 원가 합산 |
| 쿠폰할인 | `O.coupon_discount_price` | Orders 레벨 |
| 적립금사용 | `O.points_spent_amount` | Orders 레벨 |
| 배송실비 | 건당 **2,200원** 고정 | 택배 실비 |
| 카드수수료 | `O.payment_amount × 3.3%` | 실결제금액 기준 고정률 |

### 배송 유형별 차이

| 유형 | 총매출 | 배송 손익 |
|------|--------|-----------|
| 무료배송 | 상품매출만 | -2,200원 (순비용) |
| 유료배송 | 상품매출 + 3,000원 | +800원 (3,000 - 2,200) |

## 테이블 관계 및 조인 경로

### 관련 테이블 (약어)

| 약어 | 테이블 | 역할 |
|------|--------|------|
| O | `Cafe24Orders` | 주문 헤더 (매출, 할인, 결제) |
| D | `Cafe24OrdersDetail` | 주문 상세 (품목, 수량, 결제) |
| P | `Product` | 상품 마스터 |
| PB | `ProductBox` | 상품 박스 (ERPCode, 원가) |

### 조인 경로 (원가 연결)

```
Cafe24OrdersDetail (D)
  └─ D.ProductUniqueCode
       → Product.UniqueCode (P)
            → Product.ProductID
                 → ProductBox.ProductID (PB)
                      → PB.UnitCostKRW
```

### 1:N 처리 (UniqueCode → ProductBox)

하나의 상품(UniqueCode)에 여러 ProductBox(ERPCode)가 존재할 수 있다.
`ROW_NUMBER()`로 상품당 1개만 선택:

**우선순위:**
1. `QuantityInBox = 1` (단품 박스 우선)
2. `BoxID` 오름차순 (먼저 등록된 것)
3. `UnitCostKRW > 0` 인 것만 대상

```sql
ROW_NUMBER() OVER (
    PARTITION BY p.UniqueCode
    ORDER BY
        CASE WHEN pb.QuantityInBox = 1 THEN 0 ELSE 1 END,
        pb.BoxID
) AS rn
-- WHERE rn = 1 로 사용
```

## 쿼리 구조 (4번 - 주문별 공헌이익)

### CTE 흐름

```
[1] UnitCostPerProduct
    Product + ProductBox → 상품당 원가 1개 선택 (1:N 해소)

[2] OrderUnitCost
    Cafe24OrdersDetail + UnitCostPerProduct
    → 주문별 원가 합산 (SUM(quantity × UnitCostKRW))

[3] 메인 SELECT
    Cafe24Orders + OrderUnitCost
    → 주문별 공헌이익 = 총매출 - 비용 합계
```

### 필터 조건

| 조건 | 설명 |
|------|------|
| `ISNULL(o.canceled, 0) = 0` | 취소 주문 제외 |
| `o.paid = 1` | 결제 완료 건만 |
| `d.order_status NOT IN (...)` | 상세 레벨 취소 상태 제외 |

## 분석 단위별 쿼리 목록

| 번호 | 쿼리 | 단위 | 용도 |
|------|------|------|------|
| [1] | 매핑 커버리지 확인 | - | ProductUniqueCode → 원가 연결률 검증 |
| [2] | 원가 없는 상품 목록 | 상품 | 미매핑 상품 추적 |
| [3] | 1:N 현황 확인 | 상품 | UniqueCode별 ProductBox 개수 파악 |
| [4] | 주문별 공헌이익 | **주문** | 핵심 - 주문 1건 = 1행 |
| [5] | SKU별 원가 기여 | **품목** | 주문 내 상품별 원가 비중 (매출 배분 없음) |
| [6] | 월별 공헌이익 집계 | **월** | 월별 총매출/총원가/총공헌이익 |

## 방안 3 (하이브리드) 설계 원칙

- **주문 단위**: 공헌이익 **정확 계산** (O 레벨 데이터 활용)
- **SKU 단위**: 원가 비중만 분석 (매출 배분하지 않음)
  - `D.product_price`가 옵션 추가금액 미반영으로 매출 대용 불가
  - `D.payment_amount`는 참고용으로만 출력

## 추후 확장 예정

| 항목 | 설명 |
|------|------|
| 광고비 | 채널별/캠페인별 광고비 배분 |
| 공동구매 수수료 | 채널 수수료율 적용 |
| 웹앱 섹션 | 자사몰 분석 대시보드 (월별 집계, 주문별 상세) |
