-- ============================================
-- 상품 불출 관리 테이블 생성
-- WithdrawalPlan: 불출 계획 (주문번호 기준 헤더)
-- WithdrawalPlanItem: 불출 계획 상품 (상세)
-- ============================================

-- 1. WithdrawalPlan (불출 계획 헤더)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'WithdrawalPlan')
BEGIN
    CREATE TABLE [dbo].[WithdrawalPlan] (
        PlanID          INT IDENTITY(1,1) PRIMARY KEY,
        OrderNo         NVARCHAR(50) NOT NULL,           -- 주문번호
        Title           NVARCHAR(200) NULL,              -- 건명
        Type            NVARCHAR(50) NOT NULL,           -- 사용유형 (업체샘플, 증정 등)
        Status          NVARCHAR(20) NOT NULL DEFAULT 'DRAFT',  -- DRAFT / PENDING / APPROVED / REJECTED
        OrdererName     NVARCHAR(100) NULL,              -- 주문자 이름
        RecipientName   NVARCHAR(100) NULL,              -- 받는분 이름
        Phone1          NVARCHAR(30) NULL,               -- 전화번호1
        Phone2          NVARCHAR(30) NULL,               -- 전화번호2
        Address1        NVARCHAR(500) NULL,              -- 주소1
        Address2        NVARCHAR(500) NULL,              -- 주소2
        DeliveryMethod  NVARCHAR(50) NULL DEFAULT N'택배', -- 배송방식
        DeliveryMessage NVARCHAR(500) NULL,              -- 배송메세지
        DesiredDate     DATE NULL,                       -- 출고희망일
        TrackingNo      NVARCHAR(100) NULL,              -- 송장번호
        Notes           NVARCHAR(1000) NULL,             -- 관리메모
        RequestedBy     INT NULL,                        -- 신청자 (User FK)
        ApprovedBy      INT NULL,                        -- 승인자 (User FK)
        ApprovalDate    DATETIME NULL,                   -- 승인일시
        RejectionReason NVARCHAR(500) NULL,              -- 반려사유
        CreatedDate     DATETIME NOT NULL DEFAULT GETDATE(),
        UpdatedDate     DATETIME NOT NULL DEFAULT GETDATE()
    );

    CREATE INDEX IX_WithdrawalPlan_OrderNo ON [dbo].[WithdrawalPlan](OrderNo);
    CREATE INDEX IX_WithdrawalPlan_Status ON [dbo].[WithdrawalPlan](Status);
    CREATE INDEX IX_WithdrawalPlan_Type ON [dbo].[WithdrawalPlan](Type);
    CREATE INDEX IX_WithdrawalPlan_DesiredDate ON [dbo].[WithdrawalPlan](DesiredDate);
    CREATE INDEX IX_WithdrawalPlan_RequestedBy ON [dbo].[WithdrawalPlan](RequestedBy);

    PRINT 'WithdrawalPlan 테이블 생성 완료';
END
ELSE
    PRINT 'WithdrawalPlan 테이블이 이미 존재합니다';
GO

-- 2. WithdrawalPlanItem (불출 계획 상품)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'WithdrawalPlanItem')
BEGIN
    CREATE TABLE [dbo].[WithdrawalPlanItem] (
        ItemID          INT IDENTITY(1,1) PRIMARY KEY,
        PlanID          INT NOT NULL,                    -- FK → WithdrawalPlan
        ProductName     NVARCHAR(200) NOT NULL,          -- 상품명
        BaseBarcode     NVARCHAR(50) NULL,               -- 바코드 (Product.BaseBarcode에서 자동)
        UniqueCode      NVARCHAR(50) NULL,               -- 고유코드 (Product.UniqueCode에서 자동)
        Quantity        INT NOT NULL DEFAULT 1,          -- 수량
        Notes           NVARCHAR(500) NULL,              -- 비고
        CreatedDate     DATETIME NOT NULL DEFAULT GETDATE(),

        CONSTRAINT FK_WithdrawalPlanItem_Plan
            FOREIGN KEY (PlanID) REFERENCES [dbo].[WithdrawalPlan](PlanID)
            ON DELETE CASCADE
    );

    CREATE INDEX IX_WithdrawalPlanItem_PlanID ON [dbo].[WithdrawalPlanItem](PlanID);
    CREATE INDEX IX_WithdrawalPlanItem_ProductName ON [dbo].[WithdrawalPlanItem](ProductName);

    PRINT 'WithdrawalPlanItem 테이블 생성 완료';
END
ELSE
    PRINT 'WithdrawalPlanItem 테이블이 이미 존재합니다';
GO