-- =====================================================
-- Irregular → Expected3PIrregular 마이그레이션
-- 비정기 관리 시스템을 위탁 예상 매출 체계로 편입
-- =====================================================
-- 실행 전 주의사항:
--   1. 반드시 DB 백업 후 실행할 것
--   2. Expected3PIrregularProduct (구 TargetIrregularProduct) 백업 완료 확인
--   3. 웹앱 서비스 중지 후 실행 권장
-- =====================================================

BEGIN TRANSACTION;

BEGIN TRY

    -- =====================================================
    -- Step 1: 구 Expected3PIrregularProduct 테이블 삭제
    -- (Phase 1에서 rename한 TargetIrregularProduct, 백업 완료)
    -- =====================================================
    IF OBJECT_ID('dbo.Expected3PIrregularProduct', 'U') IS NOT NULL
    BEGIN
        PRINT '>> Step 1: Expected3PIrregularProduct (구 TargetIrregularProduct) 삭제';
        DROP TABLE dbo.Expected3PIrregularProduct;
        PRINT '   [OK] 삭제 완료';
    END
    ELSE
    BEGIN
        PRINT '>> Step 1: Expected3PIrregularProduct 테이블이 존재하지 않음 - SKIP';
    END

    -- =====================================================
    -- Step 2: 테이블 Rename
    -- Irregular → Expected3PIrregular
    -- IrregularProduct → Expected3PIrregularProduct
    -- (IrregularType 테이블은 유지)
    -- =====================================================
    PRINT '';
    PRINT '>> Step 2: 테이블 Rename';

    IF OBJECT_ID('dbo.Irregular', 'U') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.Irregular', 'Expected3PIrregular';
        PRINT '   [OK] Irregular → Expected3PIrregular';
    END
    ELSE
    BEGIN
        PRINT '   [SKIP] Irregular 테이블이 존재하지 않음';
    END

    IF OBJECT_ID('dbo.IrregularProduct', 'U') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.IrregularProduct', 'Expected3PIrregularProduct';
        PRINT '   [OK] IrregularProduct → Expected3PIrregularProduct';
    END
    ELSE
    BEGIN
        PRINT '   [SKIP] IrregularProduct 테이블이 존재하지 않음';
    END

    -- =====================================================
    -- Step 3: 컬럼 Rename - Expected3PIrregular
    -- IrregularID → Expected3PIrregularID (PK)
    -- (IrregularName, IrregularType 등 데이터 컬럼은 유지)
    -- =====================================================
    PRINT '';
    PRINT '>> Step 3: Expected3PIrregular 컬럼 Rename';

    IF COL_LENGTH('dbo.Expected3PIrregular', 'IrregularID') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.Expected3PIrregular.IrregularID', 'Expected3PIrregularID', 'COLUMN';
        PRINT '   [OK] IrregularID → Expected3PIrregularID';
    END

    -- =====================================================
    -- Step 4: 컬럼 Rename - Expected3PIrregularProduct
    -- IrregularProductID → Expected3PIrregularProductID (PK)
    -- IrregularID → Expected3PIrregularID (FK)
    -- (IrregularPrice 등 데이터 컬럼은 유지)
    -- =====================================================
    PRINT '';
    PRINT '>> Step 4: Expected3PIrregularProduct 컬럼 Rename';

    IF COL_LENGTH('dbo.Expected3PIrregularProduct', 'IrregularProductID') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.Expected3PIrregularProduct.IrregularProductID', 'Expected3PIrregularProductID', 'COLUMN';
        PRINT '   [OK] IrregularProductID → Expected3PIrregularProductID';
    END

    IF COL_LENGTH('dbo.Expected3PIrregularProduct', 'IrregularID') IS NOT NULL
    BEGIN
        EXEC sp_rename 'dbo.Expected3PIrregularProduct.IrregularID', 'Expected3PIrregularID', 'COLUMN';
        PRINT '   [OK] IrregularID → Expected3PIrregularID (FK)';
    END

    -- =====================================================
    -- Step 5: 검증
    -- =====================================================
    PRINT '';
    PRINT '>> Step 5: 검증';
    PRINT '';

    PRINT '--- Expected3PIrregular 컬럼 목록 ---';
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Expected3PIrregular'
    ORDER BY ORDINAL_POSITION;

    PRINT '';
    PRINT '--- Expected3PIrregularProduct 컬럼 목록 ---';
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Expected3PIrregularProduct'
    ORDER BY ORDINAL_POSITION;

    PRINT '';
    PRINT '--- IrregularType 테이블 (유지됨) ---';
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'IrregularType'
    ORDER BY ORDINAL_POSITION;

    PRINT '';
    PRINT '========================================';
    PRINT '  Irregular → Expected3PIrregular 마이그레이션 완료!';
    PRINT '  변경된 테이블: Expected3PIrregular, Expected3PIrregularProduct';
    PRINT '  유지된 테이블: IrregularType';
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
