-- ================================================
-- Promotion/PromotionProduct 테이블 컬럼명 변경
-- TargetSalesAmount → ExpectedSalesAmount
-- TargetQuantity → ExpectedQuantity
-- ================================================

-- 1. Promotion 테이블 컬럼명 변경
EXEC sp_rename 'dbo.Promotion.TargetSalesAmount', 'ExpectedSalesAmount', 'COLUMN';
EXEC sp_rename 'dbo.Promotion.TargetQuantity', 'ExpectedQuantity', 'COLUMN';
GO

-- 2. PromotionProduct 테이블 컬럼명 변경
EXEC sp_rename 'dbo.PromotionProduct.TargetSalesAmount', 'ExpectedSalesAmount', 'COLUMN';
EXEC sp_rename 'dbo.PromotionProduct.TargetQuantity', 'ExpectedQuantity', 'COLUMN';
GO

-- ================================================
-- 확인 쿼리
-- ================================================
-- EXEC sp_help 'dbo.Promotion';
-- EXEC sp_help 'dbo.PromotionProduct';
