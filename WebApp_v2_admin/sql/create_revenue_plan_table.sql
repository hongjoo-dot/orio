-- =====================================================
-- REVENUE_PLAN 테이블 생성
-- 예상매출(EXPECTED) + 목표매출(TARGET) 통합 테이블
-- =====================================================

-- 테이블 생성
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'RevenuePlan')
BEGIN
    CREATE TABLE [dbo].[RevenuePlan] (
        -- PK
        [PlanID]        INT IDENTITY(1,1) PRIMARY KEY,

        -- 기간
        [Date]          DATE NOT NULL,

        -- 브랜드 (FK)
        [BrandID]       INT NOT NULL,

        -- 채널 (FK)
        [ChannelID]     INT NOT NULL,

        -- 유형: 'TARGET' (목표) / 'EXPECTED' (예상)
        [PlanType]      NVARCHAR(20) NOT NULL,

        -- 금액
        [Amount]        DECIMAL(18,2) NOT NULL DEFAULT 0,

        -- 감사 필드
        [CreatedAt]     DATETIME2 DEFAULT GETDATE(),
        [UpdatedAt]     DATETIME2 DEFAULT GETDATE(),

        -- 제약조건
        CONSTRAINT [FK_RevenuePlan_Brand] FOREIGN KEY ([BrandID])
            REFERENCES [dbo].[Brand]([BrandID]),
        CONSTRAINT [FK_RevenuePlan_Channel] FOREIGN KEY ([ChannelID])
            REFERENCES [dbo].[Channel]([ChannelID]),
        CONSTRAINT [CK_RevenuePlan_PlanType] CHECK ([PlanType] IN ('TARGET', 'EXPECTED'))
    );

    PRINT 'RevenuePlan 테이블 생성 완료';
END
ELSE
BEGIN
    PRINT 'RevenuePlan 테이블이 이미 존재합니다';
END
GO

-- 인덱스 생성
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_RevenuePlan_Date_Brand_Channel')
BEGIN
    CREATE INDEX [IX_RevenuePlan_Date_Brand_Channel]
    ON [dbo].[RevenuePlan] ([Date], [BrandID], [ChannelID], [PlanType]);
    PRINT '인덱스 IX_RevenuePlan_Date_Brand_Channel 생성 완료';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_RevenuePlan_PlanType')
BEGIN
    CREATE INDEX [IX_RevenuePlan_PlanType]
    ON [dbo].[RevenuePlan] ([PlanType]);
    PRINT '인덱스 IX_RevenuePlan_PlanType 생성 완료';
END
GO

-- 중복 방지를 위한 유니크 제약조건 (날짜 + 브랜드 + 채널 + 유형 조합은 유일해야 함)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'UQ_RevenuePlan_Unique')
BEGIN
    CREATE UNIQUE INDEX [UQ_RevenuePlan_Unique]
    ON [dbo].[RevenuePlan] ([Date], [BrandID], [ChannelID], [PlanType]);
    PRINT '유니크 인덱스 UQ_RevenuePlan_Unique 생성 완료';
END
GO
