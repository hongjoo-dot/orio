-- ============================================================
-- InputMonth (Round) 시스템 마이그레이션
-- 모든 예상 매출 테이블에 InputMonth 컬럼 추가
-- ============================================================
-- InputMonth = 입력 월 (YYYY-MM), 실무자가 선택
-- 정기: Unique Key에 포함 (같은 월/채널/상품이 다른 InputMonth에 존재 가능)
-- 비정기: 메타데이터 (마스터에만 추가, 상품은 마스터에서 상속)
-- ============================================================
-- NOTE: ALTER TABLE ADD 후 같은 배치에서 새 컬럼 참조 시
--       SQL Server 컴파일 에러 발생 → EXEC sp_executesql 사용
-- ============================================================

BEGIN TRANSACTION;

BEGIN TRY

    -- =====================================================
    -- 1. Expected3PRegularProduct - InputMonth 추가
    -- =====================================================
    PRINT '>> 1. Expected3PRegularProduct에 InputMonth 추가';

    IF COL_LENGTH('dbo.Expected3PRegularProduct', 'InputMonth') IS NULL
    BEGIN
        ALTER TABLE [dbo].[Expected3PRegularProduct]
            ADD InputMonth nvarchar(7) NULL;
        PRINT '   [OK] InputMonth 컬럼 추가';

        -- 기존 데이터: Date에서 InputMonth 파생 (동적 SQL로 실행)
        EXEC sp_executesql N'
            UPDATE [dbo].[Expected3PRegularProduct]
            SET InputMonth = FORMAT([Date], ''yyyy-MM'')
            WHERE InputMonth IS NULL;
        ';
        PRINT '   [OK] 기존 데이터 InputMonth 채움';

        -- NOT NULL 제약 추가 (동적 SQL로 실행)
        EXEC sp_executesql N'
            ALTER TABLE [dbo].[Expected3PRegularProduct]
                ALTER COLUMN InputMonth nvarchar(7) NOT NULL;
        ';
        PRINT '   [OK] NOT NULL 제약 추가';

        -- 기존 Unique 제약 삭제 후 새로 생성
        IF EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'UQ_Exp3PRegular')
        BEGIN
            ALTER TABLE [dbo].[Expected3PRegularProduct]
                DROP CONSTRAINT UQ_Exp3PRegular;
            PRINT '   [OK] 기존 UQ_Exp3PRegular 제약 삭제';
        END

        EXEC sp_executesql N'
            ALTER TABLE [dbo].[Expected3PRegularProduct]
                ADD CONSTRAINT UQ_Exp3PRegular UNIQUE ([Date], UniqueCode, ChannelID, InputMonth);
        ';
        PRINT '   [OK] 새 Unique 제약 생성 (Date, UniqueCode, ChannelID, InputMonth)';
    END
    ELSE
    BEGIN
        PRINT '   [SKIP] InputMonth 이미 존재';
    END

    -- =====================================================
    -- 2. Expected1PRegularProduct - InputMonth 추가
    -- =====================================================
    PRINT '';
    PRINT '>> 2. Expected1PRegularProduct에 InputMonth 추가';

    IF COL_LENGTH('dbo.Expected1PRegularProduct', 'InputMonth') IS NULL
    BEGIN
        ALTER TABLE [dbo].[Expected1PRegularProduct]
            ADD InputMonth nvarchar(7) NULL;
        PRINT '   [OK] InputMonth 컬럼 추가';

        -- 기존 데이터: Date에서 InputMonth 파생 (동적 SQL로 실행)
        EXEC sp_executesql N'
            UPDATE [dbo].[Expected1PRegularProduct]
            SET InputMonth = FORMAT([Date], ''yyyy-MM'')
            WHERE InputMonth IS NULL;
        ';
        PRINT '   [OK] 기존 데이터 InputMonth 채움';

        -- NOT NULL 제약 추가 (동적 SQL로 실행)
        EXEC sp_executesql N'
            ALTER TABLE [dbo].[Expected1PRegularProduct]
                ALTER COLUMN InputMonth nvarchar(7) NOT NULL;
        ';
        PRINT '   [OK] NOT NULL 제약 추가';

        -- 기존 Unique 제약 삭제 후 새로 생성
        IF EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'UQ_Exp1PRegular')
        BEGIN
            ALTER TABLE [dbo].[Expected1PRegularProduct]
                DROP CONSTRAINT UQ_Exp1PRegular;
            PRINT '   [OK] 기존 UQ_Exp1PRegular 제약 삭제';
        END

        EXEC sp_executesql N'
            ALTER TABLE [dbo].[Expected1PRegularProduct]
                ADD CONSTRAINT UQ_Exp1PRegular UNIQUE ([Date], UniqueCode, ChannelID, InputMonth);
        ';
        PRINT '   [OK] 새 Unique 제약 생성 (Date, UniqueCode, ChannelID, InputMonth)';
    END
    ELSE
    BEGIN
        PRINT '   [SKIP] InputMonth 이미 존재';
    END

    -- =====================================================
    -- 3. Expected3PIrregular - InputMonth 추가 (메타데이터)
    -- =====================================================
    PRINT '';
    PRINT '>> 3. Expected3PIrregular에 InputMonth 추가';

    IF COL_LENGTH('dbo.Expected3PIrregular', 'InputMonth') IS NULL
    BEGIN
        ALTER TABLE [dbo].[Expected3PIrregular]
            ADD InputMonth nvarchar(7) NULL;
        PRINT '   [OK] InputMonth 컬럼 추가';

        -- 기존 데이터: StartDate에서 InputMonth 파생 (동적 SQL로 실행)
        EXEC sp_executesql N'
            UPDATE [dbo].[Expected3PIrregular]
            SET InputMonth = FORMAT(StartDate, ''yyyy-MM'')
            WHERE InputMonth IS NULL;
        ';
        PRINT '   [OK] 기존 데이터 InputMonth 채움';
    END
    ELSE
    BEGIN
        PRINT '   [SKIP] InputMonth 이미 존재';
    END

    -- =====================================================
    -- 4. Expected1PIrregular - InputMonth 추가 (메타데이터)
    -- =====================================================
    PRINT '';
    PRINT '>> 4. Expected1PIrregular에 InputMonth 추가';

    IF COL_LENGTH('dbo.Expected1PIrregular', 'InputMonth') IS NULL
    BEGIN
        ALTER TABLE [dbo].[Expected1PIrregular]
            ADD InputMonth nvarchar(7) NULL;
        PRINT '   [OK] InputMonth 컬럼 추가';

        -- 기존 데이터: StartDate에서 InputMonth 파생 (동적 SQL로 실행)
        EXEC sp_executesql N'
            UPDATE [dbo].[Expected1PIrregular]
            SET InputMonth = FORMAT(StartDate, ''yyyy-MM'')
            WHERE InputMonth IS NULL;
        ';
        PRINT '   [OK] 기존 데이터 InputMonth 채움';
    END
    ELSE
    BEGIN
        PRINT '   [SKIP] InputMonth 이미 존재';
    END

    -- =====================================================
    -- 5. SystemConfig - Slack 알림 설정 추가
    -- =====================================================
    PRINT '';
    PRINT '>> 5. SystemConfig 알림 설정 추가';

    -- Slack Webhook URL
    IF NOT EXISTS (SELECT 1 FROM [dbo].[SystemConfig] WHERE Category = 'Notification' AND ConfigKey = 'SlackWebhookURL')
    BEGIN
        INSERT INTO [dbo].[SystemConfig] (Category, ConfigKey, ConfigValue, DataType, Description, IsActive, CreatedDate, UpdatedDate, UpdatedBy)
        VALUES ('Notification', 'SlackWebhookURL', '', 'string', 'Slack Webhook URL (예상 매출 알림용)', 1, GETDATE(), GETDATE(), 'SYSTEM');
        PRINT '   [OK] SlackWebhookURL 설정 추가';
    END
    ELSE PRINT '   [SKIP] SlackWebhookURL 이미 존재';

    -- 예상 매출 알림 활성화 여부
    IF NOT EXISTS (SELECT 1 FROM [dbo].[SystemConfig] WHERE Category = 'Notification' AND ConfigKey = 'ExpectedSalesNotification')
    BEGIN
        INSERT INTO [dbo].[SystemConfig] (Category, ConfigKey, ConfigValue, DataType, Description, IsActive, CreatedDate, UpdatedDate, UpdatedBy)
        VALUES ('Notification', 'ExpectedSalesNotification', 'true', 'bool', '예상 매출 업로드 시 Slack 알림 전송 여부', 1, GETDATE(), GETDATE(), 'SYSTEM');
        PRINT '   [OK] ExpectedSalesNotification 설정 추가';
    END
    ELSE PRINT '   [SKIP] ExpectedSalesNotification 이미 존재';

    -- =====================================================
    -- 6. 검증
    -- =====================================================
    PRINT '';
    PRINT '>> 6. 검증';

    SELECT 'Expected3PRegularProduct' AS TableName, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Expected3PRegularProduct' AND COLUMN_NAME = 'InputMonth';

    SELECT 'Expected1PRegularProduct' AS TableName, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Expected1PRegularProduct' AND COLUMN_NAME = 'InputMonth';

    SELECT 'Expected3PIrregular' AS TableName, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Expected3PIrregular' AND COLUMN_NAME = 'InputMonth';

    SELECT 'Expected1PIrregular' AS TableName, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Expected1PIrregular' AND COLUMN_NAME = 'InputMonth';

    -- Unique 제약 확인
    SELECT tc.TABLE_NAME, tc.CONSTRAINT_NAME, kcu.COLUMN_NAME
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
    JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
        ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
    WHERE tc.CONSTRAINT_TYPE = 'UNIQUE'
        AND tc.TABLE_NAME IN ('Expected3PRegularProduct', 'Expected1PRegularProduct')
    ORDER BY tc.TABLE_NAME, kcu.ORDINAL_POSITION;

    PRINT '';
    PRINT '========================================';
    PRINT '  InputMonth 마이그레이션 완료!';
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
