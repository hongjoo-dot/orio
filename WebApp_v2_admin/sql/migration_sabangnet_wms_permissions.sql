-- ============================================================
-- 사방넷 WMS 모듈 권한 등록
-- Permission 테이블에 모듈+액션 추가 후 RolePermission에 역할별 연결
-- ============================================================

-- 1. Permission 등록 (중복 방지)
IF NOT EXISTS (SELECT 1 FROM [dbo].[Permission] WHERE Module = 'SabangnetInventory' AND [Action] = 'READ')
    INSERT INTO [dbo].[Permission] (Module, [Action], Name, Description) VALUES (N'SabangnetInventory', N'READ', N'WMS 재고 조회', N'사방넷 풀필먼트 재고 스냅샷 조회');

IF NOT EXISTS (SELECT 1 FROM [dbo].[Permission] WHERE Module = 'SabangnetInbound' AND [Action] = 'READ')
    INSERT INTO [dbo].[Permission] (Module, [Action], Name, Description) VALUES (N'SabangnetInbound', N'READ', N'WMS 입고 조회', N'사방넷 풀필먼트 입고예정/작업내역 조회');

PRINT N'✅ Permission 등록 완료';

-- 2. RolePermission 연결 (Admin=1, Manager=2, Viewer=3 가정)
DECLARE @InvReadID INT = (SELECT PermissionID FROM [dbo].[Permission] WHERE Module = 'SabangnetInventory' AND [Action] = 'READ');
DECLARE @InbReadID INT = (SELECT PermissionID FROM [dbo].[Permission] WHERE Module = 'SabangnetInbound' AND [Action] = 'READ');

-- Admin
IF NOT EXISTS (SELECT 1 FROM [dbo].[RolePermission] WHERE RoleID = 1 AND PermissionID = @InvReadID)
    INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID) VALUES (1, @InvReadID);
IF NOT EXISTS (SELECT 1 FROM [dbo].[RolePermission] WHERE RoleID = 1 AND PermissionID = @InbReadID)
    INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID) VALUES (1, @InbReadID);

-- Manager
IF NOT EXISTS (SELECT 1 FROM [dbo].[RolePermission] WHERE RoleID = 2 AND PermissionID = @InvReadID)
    INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID) VALUES (2, @InvReadID);
IF NOT EXISTS (SELECT 1 FROM [dbo].[RolePermission] WHERE RoleID = 2 AND PermissionID = @InbReadID)
    INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID) VALUES (2, @InbReadID);

-- Viewer
IF NOT EXISTS (SELECT 1 FROM [dbo].[RolePermission] WHERE RoleID = 3 AND PermissionID = @InvReadID)
    INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID) VALUES (3, @InvReadID);
IF NOT EXISTS (SELECT 1 FROM [dbo].[RolePermission] WHERE RoleID = 3 AND PermissionID = @InbReadID)
    INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID) VALUES (3, @InbReadID);

PRINT N'✅ RolePermission 연결 완료 (Admin, Manager, Viewer 모두 READ 권한)';
GO

-- ============================================================
-- 3. SystemConfig에 사방넷 풀필먼트 API 인증 정보 등록
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM [dbo].[SystemConfig] WHERE Category = N'SabangnetFBS' AND ConfigKey = N'API_ACCESS_KEY')
    INSERT INTO [dbo].[SystemConfig] (Category, ConfigKey, ConfigValue, DataType, Description, IsActive)
    VALUES (N'SabangnetFBS', N'API_ACCESS_KEY', N'OohCX4Mnv6FPs1Ce', N'string', N'사방넷 풀필먼트 API Access Key', 1);

IF NOT EXISTS (SELECT 1 FROM [dbo].[SystemConfig] WHERE Category = N'SabangnetFBS' AND ConfigKey = N'API_SECRET_KEY')
    INSERT INTO [dbo].[SystemConfig] (Category, ConfigKey, ConfigValue, DataType, Description, IsActive)
    VALUES (N'SabangnetFBS', N'API_SECRET_KEY', N'4qmR6LSHUf2gJmzYIVXg', N'string', N'사방넷 풀필먼트 API Secret Key', 1);

IF NOT EXISTS (SELECT 1 FROM [dbo].[SystemConfig] WHERE Category = N'SabangnetFBS' AND ConfigKey = N'COMPANY_CODE')
    INSERT INTO [dbo].[SystemConfig] (Category, ConfigKey, ConfigValue, DataType, Description, IsActive)
    VALUES (N'SabangnetFBS', N'COMPANY_CODE', N'U7392', N'string', N'사방넷 풀필먼트 회사코드', 1);

IF NOT EXISTS (SELECT 1 FROM [dbo].[SystemConfig] WHERE Category = N'SabangnetFBS' AND ConfigKey = N'MEMBER_ID')
    INSERT INTO [dbo].[SystemConfig] (Category, ConfigKey, ConfigValue, DataType, Description, IsActive)
    VALUES (N'SabangnetFBS', N'MEMBER_ID', N'2', N'string', N'사방넷 풀필먼트 고객사 ID', 1);

IF NOT EXISTS (SELECT 1 FROM [dbo].[SystemConfig] WHERE Category = N'SabangnetFBS' AND ConfigKey = N'API_HOST')
    INSERT INTO [dbo].[SystemConfig] (Category, ConfigKey, ConfigValue, DataType, Description, IsActive)
    VALUES (N'SabangnetFBS', N'API_HOST', N'https://napi.sbfulfillment.co.kr', N'string', N'사방넷 풀필먼트 API 호스트', 1);

PRINT N'✅ SystemConfig 등록 완료 (SabangnetFBS 카테고리)';
GO
