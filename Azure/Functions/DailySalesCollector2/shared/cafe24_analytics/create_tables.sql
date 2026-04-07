-- Cafe24 Analytics 유입경로 테이블 생성
-- 실행 대상: Azure SQL Database (oriodatabase)

-- 1. 도메인별 유입 + 매출
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Cafe24VisitpathDomains')
CREATE TABLE Cafe24VisitpathDomains (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    Date DATE NOT NULL,
    Domain NVARCHAR(500) NOT NULL,
    VisitCount INT NULL,
    OrderCount INT NULL,
    OrderAmount BIGINT NULL,
    CollectedDate DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_VisitpathDomains_Date_Domain UNIQUE (Date, Domain)
);
GO

-- 2. 광고별 유입 + 매출
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Cafe24VisitpathAds')
CREATE TABLE Cafe24VisitpathAds (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    Date DATE NOT NULL,
    Ad NVARCHAR(500) NOT NULL,
    VisitCount INT NULL,
    OrderCount INT NULL,
    OrderAmount BIGINT NULL,
    JoinCount INT NULL,
    CollectedDate DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_VisitpathAds_Date_Ad UNIQUE (Date, Ad)
);
GO

-- 3. 키워드별 유입 + 매출
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Cafe24VisitpathKeywords')
CREATE TABLE Cafe24VisitpathKeywords (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    Date DATE NOT NULL,
    Keyword NVARCHAR(500) NOT NULL,
    VisitCount INT NULL,
    OrderCount INT NULL,
    OrderAmount BIGINT NULL,
    CollectedDate DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_VisitpathKeywords_Date_Keyword UNIQUE (Date, Keyword)
);
GO

-- 4. 일별 방문자 수
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Cafe24Visitors')
CREATE TABLE Cafe24Visitors (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    Date DATE NOT NULL,
    VisitCount INT NULL,
    FirstVisitCount INT NULL,
    ReVisitCount INT NULL,
    CollectedDate DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_Visitors_Date UNIQUE (Date)
);
GO
