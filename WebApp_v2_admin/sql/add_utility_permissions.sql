-- ============================================
-- 유틸리티(Utility) 모듈 권한 등록
-- ============================================

-- 1. Permission 테이블에 Utility 모듈 등록
INSERT INTO [dbo].[Permission] (Module, Action, Name, Description) VALUES
(N'Utility', N'READ', N'유틸리티 사용', N'피벗 해제 등 데이터 변환 도구 사용');

-- 2. Admin 역할(RoleID=1): 모든 권한
INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
SELECT 1, PermissionID FROM [dbo].[Permission]
WHERE Module = N'Utility'
  AND PermissionID NOT IN (SELECT PermissionID FROM [dbo].[RolePermission] WHERE RoleID = 1);

-- 3. Manager 역할(RoleID=2): 모든 권한
INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
SELECT 2, PermissionID FROM [dbo].[Permission]
WHERE Module = N'Utility'
  AND PermissionID NOT IN (SELECT PermissionID FROM [dbo].[RolePermission] WHERE RoleID = 2);

-- 4. Viewer 역할(RoleID=3): READ 권한
INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
SELECT 3, PermissionID FROM [dbo].[Permission]
WHERE Module = N'Utility' AND Action = N'READ'
  AND PermissionID NOT IN (SELECT PermissionID FROM [dbo].[RolePermission] WHERE RoleID = 3);

-- 확인
SELECT p.PermissionID, p.Module, p.Action, p.Name, p.Description
FROM [dbo].[Permission] p
WHERE p.Module = N'Utility'
ORDER BY p.PermissionID;
