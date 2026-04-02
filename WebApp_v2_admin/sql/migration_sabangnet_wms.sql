-- ============================================================
-- 사방넷 풀필먼트 WMS 연동 테이블 생성
-- 실행: SSMS 또는 Azure Data Studio에서 수동 실행
-- ============================================================

-- ============================================================
-- 1. 재고 스냅샷 (상품별, 하루 2회)
-- API: GET /v2/inventory/stocks
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SabangnetInventorySnapshot')
BEGIN
    CREATE TABLE [dbo].[SabangnetInventorySnapshot] (
        SnapshotID          BIGINT IDENTITY(1,1) PRIMARY KEY,
        SnapshotDate        DATE NOT NULL,
        SnapshotTime        NVARCHAR(10) NOT NULL,          -- 'AM' (11시) 또는 'PM' (18시)
        ShippingProductID   NVARCHAR(50) NOT NULL,          -- 사방넷 출고상품ID
        ProductID           INT NULL,                       -- FK → Product.ProductID
        ProductCode         NVARCHAR(100) NULL,             -- 사방넷 상품코드
        ProductName         NVARCHAR(200) NULL,             -- 사방넷 상품명
        TotalStock          INT DEFAULT 0,                  -- 총재고
        ReceivingStock      INT DEFAULT 0,                  -- 입고 재고
        NormalStock         INT DEFAULT 0,                  -- 출고가능 재고
        OrderStock          INT DEFAULT 0,                  -- 출고지시 재고
        ShippingStock       INT DEFAULT 0,                  -- 출고작업중 재고
        DamagedStock        INT DEFAULT 0,                  -- 불량 재고
        ReturnStock         INT DEFAULT 0,                  -- 반품 재고
        KeepingStock        INT DEFAULT 0,                  -- 보관 재고
        CreatedAt           DATETIME DEFAULT GETDATE(),

        CONSTRAINT UQ_InvSnapshot_Date_Time_Product UNIQUE (SnapshotDate, SnapshotTime, ShippingProductID),
        CONSTRAINT FK_InvSnapshot_Product FOREIGN KEY (ProductID) REFERENCES [dbo].[Product](ProductID)
    );

    CREATE INDEX IX_InvSnapshot_Date ON [dbo].[SabangnetInventorySnapshot](SnapshotDate);
    CREATE INDEX IX_InvSnapshot_ProductID ON [dbo].[SabangnetInventorySnapshot](ProductID);
    CREATE INDEX IX_InvSnapshot_ShippingProductID ON [dbo].[SabangnetInventorySnapshot](ShippingProductID);

    PRINT '✅ SabangnetInventorySnapshot 테이블 생성 완료';
END
ELSE
    PRINT '⏭️ SabangnetInventorySnapshot 테이블이 이미 존재합니다';
GO


-- ============================================================
-- 2. 로케이션별 재고 스냅샷
-- API: GET /v2/inventory/stock/locations
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SabangnetLocationSnapshot')
BEGIN
    CREATE TABLE [dbo].[SabangnetLocationSnapshot] (
        LocationSnapshotID  BIGINT IDENTITY(1,1) PRIMARY KEY,
        SnapshotDate        DATE NOT NULL,
        SnapshotTime        NVARCHAR(10) NOT NULL,          -- 'AM' 또는 'PM'
        ShippingProductID   NVARCHAR(50) NOT NULL,
        ProductID           INT NULL,
        LocationID          INT NULL,                       -- 사방넷 로케이션 ID
        LocationName        NVARCHAR(100) NULL,             -- 로케이션명
        LocType             INT NULL,                       -- 1:입고, 2:출고가능, 5:반품, 6:불량, 7:보관
        ExpireDate          NVARCHAR(20) NULL,              -- 유통기한 (YYYYMMDD)
        Quantity            INT DEFAULT 0,                  -- 재고수량
        CreatedAt           DATETIME DEFAULT GETDATE(),

        CONSTRAINT FK_LocSnapshot_Product FOREIGN KEY (ProductID) REFERENCES [dbo].[Product](ProductID)
    );

    CREATE INDEX IX_LocSnapshot_Date ON [dbo].[SabangnetLocationSnapshot](SnapshotDate);
    CREATE INDEX IX_LocSnapshot_ShippingProductID ON [dbo].[SabangnetLocationSnapshot](ShippingProductID);

    PRINT '✅ SabangnetLocationSnapshot 테이블 생성 완료';
END
ELSE
    PRINT '⏭️ SabangnetLocationSnapshot 테이블이 이미 존재합니다';
GO


-- ============================================================
-- 3. 입고예정 (마스터)
-- API: GET /v2/inventory/receiving_plans
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SabangnetReceivingPlan')
BEGIN
    CREATE TABLE [dbo].[SabangnetReceivingPlan] (
        ReceivingPlanID     INT PRIMARY KEY,                -- 사방넷 입고예정 ID (API PK)
        MemberID            NVARCHAR(50) NULL,              -- 고객사 ID
        ReceivingPlanCode   NVARCHAR(50) NULL,              -- 입고예정 코드
        PlanDate            NVARCHAR(20) NULL,              -- 입고예정일 (YYYYMMDD)
        PlanStatus          INT NULL,                       -- 1:예정, 2:검수중, 3:완료, 4:취소
        CompleteDt          NVARCHAR(50) NULL,              -- 완료일시
        Memo                NVARCHAR(500) NULL,             -- 메모
        LastSyncedAt        DATETIME DEFAULT GETDATE(),     -- 마지막 동기화 시간
        CreatedAt           DATETIME DEFAULT GETDATE()
    );

    CREATE INDEX IX_RecvPlan_PlanDate ON [dbo].[SabangnetReceivingPlan](PlanDate);
    CREATE INDEX IX_RecvPlan_PlanStatus ON [dbo].[SabangnetReceivingPlan](PlanStatus);

    PRINT '✅ SabangnetReceivingPlan 테이블 생성 완료';
END
ELSE
    PRINT '⏭️ SabangnetReceivingPlan 테이블이 이미 존재합니다';
GO


-- ============================================================
-- 4. 입고예정 상품 (디테일)
-- API: GET /v2/inventory/receiving_plan/{id} → plan_product_list
--      GET /v2/inventory/receiving_plan_result/{id} → receiving_quantity
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SabangnetReceivingPlanProduct')
BEGIN
    CREATE TABLE [dbo].[SabangnetReceivingPlanProduct] (
        ID                  BIGINT IDENTITY(1,1) PRIMARY KEY,
        ReceivingPlanID     INT NOT NULL,                   -- FK → SabangnetReceivingPlan
        ShippingProductID   NVARCHAR(50) NOT NULL,          -- 출고상품 ID
        ProductID           INT NULL,                       -- FK → Product.ProductID
        Quantity            INT DEFAULT 0,                  -- 예정 수량
        ReceivingQuantity   INT NULL,                       -- 실제 입고 수량
        PlanProductStatus   INT NULL,                       -- 1:미입고, 3:부분입고, 5:완료, 9:취소
        ExpireDate          NVARCHAR(20) NULL,              -- 유통기한
        MakeDate            NVARCHAR(20) NULL,              -- 제조일자

        CONSTRAINT FK_RecvPlanProduct_Plan FOREIGN KEY (ReceivingPlanID) REFERENCES [dbo].[SabangnetReceivingPlan](ReceivingPlanID),
        CONSTRAINT FK_RecvPlanProduct_Product FOREIGN KEY (ProductID) REFERENCES [dbo].[Product](ProductID)
    );

    CREATE INDEX IX_RecvPlanProduct_PlanID ON [dbo].[SabangnetReceivingPlanProduct](ReceivingPlanID);
    CREATE INDEX IX_RecvPlanProduct_ShippingProductID ON [dbo].[SabangnetReceivingPlanProduct](ShippingProductID);

    PRINT '✅ SabangnetReceivingPlanProduct 테이블 생성 완료';
END
ELSE
    PRINT '⏭️ SabangnetReceivingPlanProduct 테이블이 이미 존재합니다';
GO


-- ============================================================
-- 5. 입고작업내역
-- API: GET /v2/inventory/receiving_works
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SabangnetReceivingWork')
BEGIN
    CREATE TABLE [dbo].[SabangnetReceivingWork] (
        WorkHistoryID       BIGINT PRIMARY KEY,             -- 사방넷 작업내역 ID (API PK)
        WorkDate            NVARCHAR(50) NULL,              -- 작업일시 (YYYY-MM-DD HH24:MI:SS)
        WorkType            INT NULL,                       -- 1:입고, 3:적치, 5:회송, 7:반품입고, 9:취소
        ReceivingType       INT NULL,                       -- 1:예정검수, 3:개별, 5:간편, 7:전수검사, 9:엑셀
        ReceivingPlanID     INT NULL,                       -- 입고예정 ID
        ShippingProductID   NVARCHAR(50) NULL,              -- 출고상품 ID
        ProductID           INT NULL,                       -- FK → Product.ProductID
        Quantity            INT DEFAULT 0,                  -- 수량
        ExpireDate          NVARCHAR(20) NULL,              -- 유통기한
        MakeDate            NVARCHAR(20) NULL,              -- 제조일자
        LocationID          INT NULL,                       -- 로케이션 ID
        BoxQuantity         INT NULL,                       -- 박스 수량
        PalletQuantity      INT NULL,                       -- 팔레트 수량
        LastSyncedAt        DATETIME DEFAULT GETDATE(),
        CreatedAt           DATETIME DEFAULT GETDATE(),

        CONSTRAINT FK_RecvWork_Product FOREIGN KEY (ProductID) REFERENCES [dbo].[Product](ProductID)
    );

    CREATE INDEX IX_RecvWork_WorkDate ON [dbo].[SabangnetReceivingWork](WorkDate);
    CREATE INDEX IX_RecvWork_WorkType ON [dbo].[SabangnetReceivingWork](WorkType);
    CREATE INDEX IX_RecvWork_ShippingProductID ON [dbo].[SabangnetReceivingWork](ShippingProductID);
    CREATE INDEX IX_RecvWork_ReceivingPlanID ON [dbo].[SabangnetReceivingWork](ReceivingPlanID);

    PRINT '✅ SabangnetReceivingWork 테이블 생성 완료';
END
ELSE
    PRINT '⏭️ SabangnetReceivingWork 테이블이 이미 존재합니다';
GO

PRINT '';
PRINT '============================================================';
PRINT '  모든 사방넷 WMS 테이블 생성 완료';
PRINT '  - SabangnetInventorySnapshot (재고 스냅샷)';
PRINT '  - SabangnetLocationSnapshot (로케이션별 재고)';
PRINT '  - SabangnetReceivingPlan (입고예정)';
PRINT '  - SabangnetReceivingPlanProduct (입고예정 상품)';
PRINT '  - SabangnetReceivingWork (입고작업내역)';
PRINT '============================================================';
GO
