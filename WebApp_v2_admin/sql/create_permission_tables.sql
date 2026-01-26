-- =====================================================
-- Permission System Tables
-- 모듈+액션 기반 RBAC 권한 시스템
-- =====================================================

-- 1. Permission 테이블 (권한 정의)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Permission')
BEGIN
    CREATE TABLE [dbo].[Permission] (
        PermissionID INT IDENTITY(1,1) PRIMARY KEY,
        Module NVARCHAR(50) NOT NULL,           -- 모듈명 (Product, Channel, Sales, Admin 등)
        Action NVARCHAR(50) NOT NULL,           -- 액션 (CREATE, READ, UPDATE, DELETE, EXPORT, UPLOAD 등)
        Name NVARCHAR(100) NOT NULL,            -- 권한 표시명 (제품 등록, 채널 삭제 등)
        Description NVARCHAR(255) NULL,         -- 설명
        CreatedDate DATETIME DEFAULT GETDATE(),

        CONSTRAINT UQ_Permission_Module_Action UNIQUE (Module, Action)
    );

    PRINT 'Permission 테이블 생성 완료';
END
GO

-- 2. RolePermission 테이블 (역할-권한 매핑)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'RolePermission')
BEGIN
    CREATE TABLE [dbo].[RolePermission] (
        RolePermissionID INT IDENTITY(1,1) PRIMARY KEY,
        RoleID INT NOT NULL,
        PermissionID INT NOT NULL,
        CreatedDate DATETIME DEFAULT GETDATE(),
        CreatedBy INT NULL,

        CONSTRAINT FK_RolePermission_Role FOREIGN KEY (RoleID)
            REFERENCES [dbo].[Role](RoleID) ON DELETE CASCADE,
        CONSTRAINT FK_RolePermission_Permission FOREIGN KEY (PermissionID)
            REFERENCES [dbo].[Permission](PermissionID) ON DELETE CASCADE,
        CONSTRAINT UQ_RolePermission UNIQUE (RoleID, PermissionID)
    );

    PRINT 'RolePermission 테이블 생성 완료';
END
GO

-- 3. 인덱스 생성
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Permission_Module')
    CREATE INDEX IX_Permission_Module ON [dbo].[Permission](Module);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_RolePermission_RoleID')
    CREATE INDEX IX_RolePermission_RoleID ON [dbo].[RolePermission](RoleID);
GO

-- =====================================================
-- 기본 권한 데이터 삽입
-- =====================================================

-- 기존 데이터 삭제 (선택적)
-- DELETE FROM [dbo].[RolePermission];
-- DELETE FROM [dbo].[Permission];

-- Permission 데이터 삽입
IF NOT EXISTS (SELECT * FROM [dbo].[Permission])
BEGIN
    INSERT INTO [dbo].[Permission] (Module, Action, Name, Description) VALUES
    -- Product 모듈
    ('Product', 'READ', '제품 조회', '제품 목록 및 상세 조회'),
    ('Product', 'CREATE', '제품 등록', '새 제품 등록'),
    ('Product', 'UPDATE', '제품 수정', '제품 정보 수정'),
    ('Product', 'DELETE', '제품 삭제', '제품 삭제'),
    ('Product', 'EXPORT', '제품 엑셀 다운로드', '제품 데이터 엑셀 내보내기'),
    ('Product', 'UPLOAD', '제품 엑셀 업로드', '제품 데이터 일괄 업로드'),

    -- Brand 모듈
    ('Brand', 'READ', '브랜드 조회', '브랜드 목록 및 상세 조회'),
    ('Brand', 'CREATE', '브랜드 등록', '새 브랜드 등록'),
    ('Brand', 'UPDATE', '브랜드 수정', '브랜드 정보 수정'),
    ('Brand', 'DELETE', '브랜드 삭제', '브랜드 삭제'),

    -- Channel 모듈
    ('Channel', 'READ', '채널 조회', '채널 목록 및 상세 조회'),
    ('Channel', 'CREATE', '채널 등록', '새 채널 등록'),
    ('Channel', 'UPDATE', '채널 수정', '채널 정보 수정'),
    ('Channel', 'DELETE', '채널 삭제', '채널 삭제'),

    -- BOM 모듈
    ('BOM', 'READ', 'BOM 조회', 'BOM 목록 및 상세 조회'),
    ('BOM', 'CREATE', 'BOM 등록', '새 BOM 등록'),
    ('BOM', 'UPDATE', 'BOM 수정', 'BOM 정보 수정'),
    ('BOM', 'DELETE', 'BOM 삭제', 'BOM 삭제'),

    -- Sales 모듈
    ('Sales', 'READ', '매출 조회', '매출 데이터 조회'),
    ('Sales', 'CREATE', '매출 등록', '매출 데이터 등록'),
    ('Sales', 'UPDATE', '매출 수정', '매출 데이터 수정'),
    ('Sales', 'DELETE', '매출 삭제', '매출 데이터 삭제'),
    ('Sales', 'SYNC', '매출 동기화', 'ERP 매출 데이터 동기화'),
    ('Sales', 'EXPORT', '매출 엑셀 다운로드', '매출 데이터 엑셀 내보내기'),

    -- Target 모듈
    ('Target', 'READ', '목표 조회', '목표 데이터 조회'),
    ('Target', 'CREATE', '목표 등록', '목표 데이터 등록'),
    ('Target', 'UPDATE', '목표 수정', '목표 데이터 수정'),
    ('Target', 'DELETE', '목표 삭제', '목표 데이터 삭제'),
    ('Target', 'UPLOAD', '목표 엑셀 업로드', '목표 데이터 일괄 업로드'),

    -- Admin 모듈 (관리자 전용)
    ('Admin', 'USER_READ', '사용자 조회', '사용자 목록 및 상세 조회'),
    ('Admin', 'USER_CREATE', '사용자 등록', '새 사용자 등록'),
    ('Admin', 'USER_UPDATE', '사용자 수정', '사용자 정보 수정'),
    ('Admin', 'USER_DELETE', '사용자 삭제', '사용자 삭제'),
    ('Admin', 'ROLE_MANAGE', '역할 관리', '역할 및 권한 설정'),
    ('Admin', 'LOG_VIEW', '활동 로그 조회', '시스템 활동 이력 조회');

    PRINT 'Permission 기본 데이터 삽입 완료';
END
GO

-- =====================================================
-- 역할별 권한 할당 (예시)
-- =====================================================

-- Admin 역할: 모든 권한
IF NOT EXISTS (SELECT * FROM [dbo].[RolePermission] WHERE RoleID = 1)
BEGIN
    INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
    SELECT 1, PermissionID FROM [dbo].[Permission];

    PRINT 'Admin 역할에 모든 권한 할당 완료';
END
GO

-- Manager 역할 (RoleID = 2): Admin 모듈 제외 모든 권한
IF NOT EXISTS (SELECT * FROM [dbo].[RolePermission] WHERE RoleID = 2)
BEGIN
    INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
    SELECT 2, PermissionID
    FROM [dbo].[Permission]
    WHERE Module != 'Admin';

    PRINT 'Manager 역할에 권한 할당 완료';
END
GO

-- Viewer 역할 (RoleID = 3): READ 권한만
IF NOT EXISTS (SELECT * FROM [dbo].[RolePermission] WHERE RoleID = 3)
BEGIN
    INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
    SELECT 3, PermissionID
    FROM [dbo].[Permission]
    WHERE Action = 'READ';

    PRINT 'Viewer 역할에 조회 권한 할당 완료';
END
GO

-- =====================================================
-- 권한 조회용 뷰 (선택)
-- =====================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_RolePermissions')
    DROP VIEW vw_RolePermissions;
GO

CREATE VIEW vw_RolePermissions AS
SELECT
    r.RoleID,
    r.Name AS RoleName,
    p.PermissionID,
    p.Module,
    p.Action,
    p.Name AS PermissionName,
    p.Module + ':' + p.Action AS PermissionCode
FROM [dbo].[Role] r
JOIN [dbo].[RolePermission] rp ON r.RoleID = rp.RoleID
JOIN [dbo].[Permission] p ON rp.PermissionID = p.PermissionID;
GO

PRINT '권한 시스템 테이블 설정 완료!';
