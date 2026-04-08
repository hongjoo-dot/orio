-- Cafe24 주문별 UTM 테이블 생성
-- 실행 대상: Azure SQL Database (oriodatabase)

-- 기존 집계 테이블 삭제
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'Cafe24VisitpathDomains')
    DROP TABLE Cafe24VisitpathDomains;

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'Cafe24VisitpathAds')
    DROP TABLE Cafe24VisitpathAds;

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'Cafe24VisitpathKeywords')
    DROP TABLE Cafe24VisitpathKeywords;

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'Cafe24Visitors')
    DROP TABLE Cafe24Visitors;

-- 주문별 UTM 테이블 생성
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Cafe24OrderUTM')
CREATE TABLE Cafe24OrderUTM (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    OrderID NVARCHAR(50) NOT NULL,
    OrderDate DATE NULL,
    Ad NVARCHAR(500) NULL,
    Keyword NVARCHAR(500) NULL,
    Medium NVARCHAR(500) NULL,
    Campaign NVARCHAR(500) NULL,
    Content NVARCHAR(1000) NULL,
    PaymentMethod NVARCHAR(100) NULL,
    OrderAmount BIGINT NULL,
    CollectedDate DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_OrderUTM_OrderID UNIQUE (OrderID)
);
