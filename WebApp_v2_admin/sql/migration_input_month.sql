-- ============================================================
-- InputMonth (Round) 시스템 마이그레이션
-- 모든 예상 매출 테이블에 InputMonth 컬럼 추가
-- ============================================================
-- 트랜잭션 없이 단계별 실행 (실패 시 즉시 에러 확인 가능)
-- ============================================================

-- =====================================================
-- 1. Expected3PRegularProduct - InputMonth 추가
-- =====================================================
PRINT '>> 1. Expected3PRegularProduct';

IF COL_LENGTH('dbo.Expected3PRegularProduct', 'InputMonth') IS NULL
BEGIN
    ALTER TABLE [dbo].[Expected3PRegularProduct] ADD InputMonth nvarchar(7) NULL;
    PRINT '   [OK] InputMonth 컬럼 추가';
END
ELSE PRINT '   [SKIP] InputMonth 이미 존재';
GO

-- 기존 데이터 백필
IF COL_LENGTH('dbo.Expected3PRegularProduct', 'InputMonth') IS NOT NULL
BEGIN
    UPDATE [dbo].[Expected3PRegularProduct]
    SET InputMonth = FORMAT([Date], 'yyyy-MM')
    WHERE InputMonth IS NULL;
    PRINT '   [OK] 기존 데이터 InputMonth 채움';

    -- NOT NULL 제약 (데이터가 모두 채워진 후)
    IF EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Expected3PRegularProduct' AND COLUMN_NAME = 'InputMonth' AND IS_NULLABLE = 'YES'
    )
    BEGIN
        ALTER TABLE [dbo].[Expected3PRegularProduct] ALTER COLUMN InputMonth nvarchar(7) NOT NULL;
        PRINT '   [OK] NOT NULL 제약 추가';
    END
END
GO

-- Unique 제약 재생성
IF COL_LENGTH('dbo.Expected3PRegularProduct', 'InputMonth') IS NOT NULL
BEGIN
    IF EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'UQ_Exp3PRegular')
    BEGIN
        ALTER TABLE [dbo].[Expected3PRegularProduct] DROP CONSTRAINT UQ_Exp3PRegular;
        PRINT '   [OK] 기존 UQ_Exp3PRegular 삭제';
    END

    IF NOT EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'UQ_Exp3PRegular')
    BEGIN
        ALTER TABLE [dbo].[Expected3PRegularProduct]
            ADD CONSTRAINT UQ_Exp3PRegular UNIQUE ([Date], UniqueCode, ChannelID, InputMonth);
        PRINT '   [OK] 새 UQ_Exp3PRegular 생성';
    END
END
GO

-- =====================================================
-- 2. Expected1PRegularProduct - InputMonth 추가
-- =====================================================
PRINT '';
PRINT '>> 2. Expected1PRegularProduct';

IF COL_LENGTH('dbo.Expected1PRegularProduct', 'InputMonth') IS NULL
BEGIN
    ALTER TABLE [dbo].[Expected1PRegularProduct] ADD InputMonth nvarchar(7) NULL;
    PRINT '   [OK] InputMonth 컬럼 추가';
END
ELSE PRINT '   [SKIP] InputMonth 이미 존재';
GO

IF COL_LENGTH('dbo.Expected1PRegularProduct', 'InputMonth') IS NOT NULL
BEGIN
    UPDATE [dbo].[Expected1PRegularProduct]
    SET InputMonth = FORMAT([Date], 'yyyy-MM')
    WHERE InputMonth IS NULL;
    PRINT '   [OK] 기존 데이터 InputMonth 채움';

    IF EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Expected1PRegularProduct' AND COLUMN_NAME = 'InputMonth' AND IS_NULLABLE = 'YES'
    )
    BEGIN
        ALTER TABLE [dbo].[Expected1PRegularProduct] ALTER COLUMN InputMonth nvarchar(7) NOT NULL;
        PRINT '   [OK] NOT NULL 제약 추가';
    END
END
GO

IF COL_LENGTH('dbo.Expected1PRegularProduct', 'InputMonth') IS NOT NULL
BEGIN
    IF EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'UQ_Exp1PRegular')
    BEGIN
        ALTER TABLE [dbo].[Expected1PRegularProduct] DROP CONSTRAINT UQ_Exp1PRegular;
        PRINT '   [OK] 기존 UQ_Exp1PRegular 삭제';
    END

    IF NOT EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'UQ_Exp1PRegular')
    BEGIN
        ALTER TABLE [dbo].[Expected1PRegularProduct]
            ADD CONSTRAINT UQ_Exp1PRegular UNIQUE ([Date], UniqueCode, ChannelID, InputMonth);
        PRINT '   [OK] 새 UQ_Exp1PRegular 생성';
    END
END
GO

-- =====================================================
-- 3. Expected3PIrregular - InputMonth 추가 (메타데이터)
-- =====================================================
PRINT '';
PRINT '>> 3. Expected3PIrregular';

IF COL_LENGTH('dbo.Expected3PIrregular', 'InputMonth') IS NULL
BEGIN
    ALTER TABLE [dbo].[Expected3PIrregular] ADD InputMonth nvarchar(7) NULL;
    PRINT '   [OK] InputMonth 컬럼 추가';
END
ELSE PRINT '   [SKIP] InputMonth 이미 존재';
GO

IF COL_LENGTH('dbo.Expected3PIrregular', 'InputMonth') IS NOT NULL
BEGIN
    UPDATE [dbo].[Expected3PIrregular]
    SET InputMonth = FORMAT(StartDate, 'yyyy-MM')
    WHERE InputMonth IS NULL;
    PRINT '   [OK] 기존 데이터 InputMonth 채움';
END
GO

-- =====================================================
-- 4. Expected1PIrregular - InputMonth 추가 (메타데이터)
-- =====================================================
PRINT '';
PRINT '>> 4. Expected1PIrregular';

IF COL_LENGTH('dbo.Expected1PIrregular', 'InputMonth') IS NULL
BEGIN
    ALTER TABLE [dbo].[Expected1PIrregular] ADD InputMonth nvarchar(7) NULL;
    PRINT '   [OK] InputMonth 컬럼 추가';
END
ELSE PRINT '   [SKIP] InputMonth 이미 존재';
GO

IF COL_LENGTH('dbo.Expected1PIrregular', 'InputMonth') IS NOT NULL
BEGIN
    UPDATE [dbo].[Expected1PIrregular]
    SET InputMonth = FORMAT(StartDate, 'yyyy-MM')
    WHERE InputMonth IS NULL;
    PRINT '   [OK] 기존 데이터 InputMonth 채움';
END
GO

-- =====================================================
-- 5. 검증
-- =====================================================
PRINT '';
PRINT '>> 5. 검증';

SELECT 'Expected3PRegularProduct' AS [Table], COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Expected3PRegularProduct' AND COLUMN_NAME = 'InputMonth';

SELECT 'Expected1PRegularProduct' AS [Table], COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Expected1PRegularProduct' AND COLUMN_NAME = 'InputMonth';

SELECT 'Expected3PIrregular' AS [Table], COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Expected3PIrregular' AND COLUMN_NAME = 'InputMonth';

SELECT 'Expected1PIrregular' AS [Table], COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Expected1PIrregular' AND COLUMN_NAME = 'InputMonth';

PRINT '';
PRINT '========================================';
PRINT '  InputMonth 마이그레이션 완료!';
PRINT '========================================';
GO