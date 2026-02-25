-- ============================================================
-- 사입(1P) 예상 매출 테이블 생성 + Permission 추가
-- ============================================================

-- 1. Expected1PRegularProduct (사입 정기 예상 매출)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Expected1PRegularProduct]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Expected1PRegularProduct] (
        Expected1PRegularID int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [Date] date NOT NULL,
        BrandID int NOT NULL,
        BrandName nvarchar(100) NULL,
        ChannelID int NOT NULL,
        ChannelName nvarchar(100) NULL,
        ERPCode nvarchar(50) NULL,
        UniqueCode nvarchar(50) NOT NULL,
        ProductName nvarchar(200) NULL,
        ExpectedAmount decimal(18,2) NULL,
        ExpectedAmountExVAT decimal(18,2) NULL,
        ExpectedQuantity int NULL,
        Notes nvarchar(MAX) NULL,
        CreatedDate datetime DEFAULT GETDATE() NULL,
        UpdatedDate datetime DEFAULT GETDATE() NULL,
        CONSTRAINT UQ_Exp1PRegular UNIQUE ([Date], UniqueCode, ChannelID)
    );
    PRINT 'Created table: Expected1PRegularProduct';
END
GO

-- 2. Expected1PIrregular (사입 비정기 마스터)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Expected1PIrregular]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Expected1PIrregular] (
        Expected1PIrregularID nvarchar(20) NOT NULL PRIMARY KEY,
        IrregularName nvarchar(200) NULL,
        IrregularType nvarchar(100) NULL,
        StartDate date NOT NULL,
        StartTime time DEFAULT '00:00:00' NOT NULL,
        EndDate date NOT NULL,
        EndTime time DEFAULT '23:59:59' NOT NULL,
        Status nvarchar(20) DEFAULT 'SCHEDULED' NULL,
        BrandID int NOT NULL,
        BrandName nvarchar(100) NULL,
        ChannelID int NOT NULL,
        ChannelName nvarchar(100) NULL,
        CommissionRate decimal(5,2) NULL,
        DiscountOwner nvarchar(20) NULL,
        CompanyShare decimal(5,2) NULL,
        ChannelShare decimal(5,2) NULL,
        ExpectedSalesAmount decimal(18,2) NULL,
        ExpectedQuantity int NULL,
        Notes nvarchar(MAX) NULL,
        CreatedDate datetime DEFAULT GETDATE() NULL,
        UpdatedDate datetime DEFAULT GETDATE() NULL
    );
    PRINT 'Created table: Expected1PIrregular';
END
GO

-- 3. Expected1PIrregularProduct (사입 비정기 상품)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Expected1PIrregularProduct]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Expected1PIrregularProduct] (
        Expected1PIrregularProductID int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        Expected1PIrregularID nvarchar(20) NOT NULL,
        ERPCode nvarchar(50) NULL,
        UniqueCode nvarchar(50) NOT NULL,
        ProductName nvarchar(200) NULL,
        SellingPrice decimal(18,2) NULL,
        IrregularPrice decimal(18,2) NULL,
        SupplyPrice decimal(18,2) NULL,
        CouponDiscountRate decimal(5,2) NULL,
        UnitCost decimal(18,2) NULL,
        LogisticsCost decimal(18,2) NULL,
        ManagementCost decimal(18,2) NULL,
        WarehouseCost decimal(18,2) NULL,
        EDICost decimal(18,2) NULL,
        MisCost decimal(18,2) NULL,
        ExpectedSalesAmount decimal(18,2) NULL,
        ExpectedQuantity int NULL,
        Notes nvarchar(MAX) NULL,
        CreatedDate datetime DEFAULT GETDATE() NULL,
        UpdatedDate datetime DEFAULT GETDATE() NULL,
        CONSTRAINT FK_Exp1PIrregProd_Irreg FOREIGN KEY (Expected1PIrregularID) REFERENCES [dbo].[Expected1PIrregular](Expected1PIrregularID)
    );
    PRINT 'Created table: Expected1PIrregularProduct';
END
GO

-- 4. Permission 추가 (Expected1PRegular)
IF NOT EXISTS (SELECT 1 FROM [dbo].[Permission] WHERE Module = 'Expected1PRegular')
BEGIN
    INSERT INTO [dbo].[Permission] (Module, [Action], Name, Description)
    SELECT 'Expected1PRegular', [Action],
           REPLACE(REPLACE(Name, '위탁', '사입'), '3P', '1P'),
           REPLACE(REPLACE(Description, '위탁', '사입'), '3P', '1P')
    FROM [dbo].[Permission]
    WHERE Module = 'Expected3PRegular';
    PRINT 'Inserted permissions for Expected1PRegular';
END
GO

-- 5. Permission 추가 (Expected1PIrregular)
IF NOT EXISTS (SELECT 1 FROM [dbo].[Permission] WHERE Module = 'Expected1PIrregular')
BEGIN
    INSERT INTO [dbo].[Permission] (Module, [Action], Name, Description)
    SELECT 'Expected1PIrregular', [Action],
           REPLACE(REPLACE(Name, '위탁', '사입'), '3P', '1P'),
           REPLACE(REPLACE(Description, '위탁', '사입'), '3P', '1P')
    FROM [dbo].[Permission]
    WHERE Module = 'Expected3PIrregular';
    PRINT 'Inserted permissions for Expected1PIrregular';
END
GO

-- 확인
SELECT Module, [Action], Name, Description
FROM [dbo].[Permission]
WHERE Module IN ('Expected1PRegular', 'Expected1PIrregular')
ORDER BY Module, [Action];
