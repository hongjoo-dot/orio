-- ============================================
-- Promotion 테이블에서 목표 관련 칼럼 삭제
-- ============================================

-- 1. IsActive의 DEFAULT 제약 조건 삭제
ALTER TABLE dbo.Promotion
DROP CONSTRAINT DF__Promotion__IsAct__3592E0D8;

-- 2. 칼럼 삭제
ALTER TABLE dbo.Promotion
DROP COLUMN TargetSalesAmount;

ALTER TABLE dbo.Promotion
DROP COLUMN TargetQuantity;

ALTER TABLE dbo.Promotion
DROP COLUMN TargetProfit;

ALTER TABLE dbo.Promotion
DROP COLUMN IsActive;
