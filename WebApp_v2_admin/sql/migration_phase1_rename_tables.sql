-- =====================================================
-- Phase 1: DB 테이블/컬럼 Rename 마이그레이션
-- 예상 매출 관리 시스템 리팩토링
-- Target → Expected, Base → Regular, 3P/1P 구분
-- =====================================================
-- 실행 전 주의사항:
--   1. 반드시 DB 백업 후 실행할 것
--   2. 웹앱 서비스 중지 후 실행 권장
--   3. 트랜잭션 내에서 실행하여 롤백 가능하도록 함
-- =====================================================

BEGIN TRANSACTION;

BEGIN TRY

    -- =====================================================
    -- Step 1: 기존 ExpectedBaseProduct 테이블 삭제
    -- (사용되지 않는 레거시 테이블)
    -- =====================================================
    IF OBJECT_ID('dbo.ExpectedBaseProduct', 'U') IS NOT NULL
    BEGIN
        PRINT '>> Step 1: ExpectedBaseProduct 테이블 삭제';
        DROP TABLE dbo.ExpectedBaseProduct;
        PRINT '   [OK] ExpectedBaseProduct 삭제 완료';
    END
    ELSE
    BEGIN
        PRINT '>> Step 1: ExpectedBaseProduct 테이블이 존재하지 않음 - SKIP';
    END

    -- =====================================================
    -- Step 2: 테이블 Rename
    -- TargetBaseProduct → Expected3PRegularProduct
    -- TargetIrregularProduct → Expected3PIrregularProduct
    -- =====================================================
    PRINT '';
    PRINT '>> Step 2: 테이블 Rename';

    IF OBJECT_ID('dbo.TargetBaseProduct', 'U') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.TargetBaseProduct', 'Expected3PRegularProduct';
        PRINT '   [OK] TargetBaseProduct → Expected3PRegularProduct';
    END
    ELSE
    BEGIN
        PRINT '   [SKIP] TargetBaseProduct가 존재하지 않음';
    END

    IF OBJECT_ID('dbo.TargetIrregularProduct', 'U') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.TargetIrregularProduct', 'Expected3PIrregularProduct';
        PRINT '   [OK] TargetIrregularProduct → Expected3PIrregularProduct';
    END
    ELSE
    BEGIN
        PRINT '   [SKIP] TargetIrregularProduct가 존재하지 않음';
    END

    -- =====================================================
    -- Step 3: 컬럼 Rename - Expected3PRegularProduct
    -- =====================================================
    PRINT '';
    PRINT '>> Step 3: Expected3PRegularProduct 컬럼 Rename';

    IF COL_LENGTH('dbo.Expected3PRegularProduct', 'TargetBaseID') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.Expected3PRegularProduct.TargetBaseID', 'Expected3PRegularID', 'COLUMN';
        PRINT '   [OK] TargetBaseID → Expected3PRegularID';
    END

    IF COL_LENGTH('dbo.Expected3PRegularProduct', 'TargetAmount') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.Expected3PRegularProduct.TargetAmount', 'ExpectedAmount', 'COLUMN';
        PRINT '   [OK] TargetAmount → ExpectedAmount';
    END

    IF COL_LENGTH('dbo.Expected3PRegularProduct', 'TargetAmountExVAT') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.Expected3PRegularProduct.TargetAmountExVAT', 'ExpectedAmountExVAT', 'COLUMN';
        PRINT '   [OK] TargetAmountExVAT → ExpectedAmountExVAT';
    END

    IF COL_LENGTH('dbo.Expected3PRegularProduct', 'TargetQuantity') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.Expected3PRegularProduct.TargetQuantity', 'ExpectedQuantity', 'COLUMN';
        PRINT '   [OK] TargetQuantity → ExpectedQuantity';
    END

    -- =====================================================
    -- Step 4: 컬럼 Rename - Expected3PIrregularProduct
    -- =====================================================
    PRINT '';
    PRINT '>> Step 4: Expected3PIrregularProduct 컬럼 Rename';

    IF COL_LENGTH('dbo.Expected3PIrregularProduct', 'TargetIrregularID') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.Expected3PIrregularProduct.TargetIrregularID', 'Expected3PIrregularID', 'COLUMN';
        PRINT '   [OK] TargetIrregularID → Expected3PIrregularID';
    END

    IF COL_LENGTH('dbo.Expected3PIrregularProduct', 'TargetAmount') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.Expected3PIrregularProduct.TargetAmount', 'ExpectedAmount', 'COLUMN';
        PRINT '   [OK] TargetAmount → ExpectedAmount';
    END

    IF COL_LENGTH('dbo.Expected3PIrregularProduct', 'TargetAmountExVAT') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.Expected3PIrregularProduct.TargetAmountExVAT', 'ExpectedAmountExVAT', 'COLUMN';
        PRINT '   [OK] TargetAmountExVAT → ExpectedAmountExVAT';
    END

    IF COL_LENGTH('dbo.Expected3PIrregularProduct', 'TargetQuantity') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.Expected3PIrregularProduct.TargetQuantity', 'ExpectedQuantity', 'COLUMN';
        PRINT '   [OK] TargetQuantity → ExpectedQuantity';
    END

    -- =====================================================
    -- Step 5: 검증 - 변경된 테이블/컬럼 확인
    -- =====================================================
    PRINT '';
    PRINT '>> Step 5: 검증';
    PRINT '';

    PRINT '--- Expected3PRegularProduct 컬럼 목록 ---';
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Expected3PRegularProduct'
    ORDER BY ORDINAL_POSITION;

    PRINT '';
    PRINT '--- Expected3PIrregularProduct 컬럼 목록 ---';
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Expected3PIrregularProduct'
    ORDER BY ORDINAL_POSITION;

    PRINT '';
    PRINT '========================================';
    PRINT '  Phase 1 마이그레이션 완료!';
    PRINT '========================================';

    COMMIT TRANSACTION;

END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    PRINT '';
    PRINT '========================================';
    PRINT '  [ERROR] 마이그레이션 실패 - 롤백됨!';
    PRINT '  Error: ' + ERROR_MESSAGE();
    PRINT '========================================';
END CATCH;
