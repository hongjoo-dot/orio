-- ============================================
-- 불출 관리(Withdrawal) 모듈 권한 등록
-- ============================================

-- 1. Permission 테이블에 Withdrawal 모듈 등록
INSERT INTO [dbo].[Permission] (Module, Action, Name, Description) VALUES
(N'Withdrawal', N'READ',   N'불출 조회',           N'불출 계획 목록 및 상세 조회'),
(N'Withdrawal', N'CREATE', N'불출 등록',           N'새 불출 계획 등록'),
(N'Withdrawal', N'UPDATE', N'불출 수정',           N'불출 계획 수정 및 상태 변경'),
(N'Withdrawal', N'DELETE', N'불출 삭제',           N'불출 계획 삭제'),
(N'Withdrawal', N'EXPORT', N'불출 엑셀 다운로드',  N'불출 데이터 엑셀 내보내기'),
(N'Withdrawal', N'UPLOAD', N'불출 엑셀 업로드',    N'불출 데이터 일괄 업로드');

-- 2. Admin 역할(RoleID=1): 모든 권한
INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
SELECT 1, PermissionID FROM [dbo].[Permission]
WHERE Module = N'Withdrawal'
  AND PermissionID NOT IN (SELECT PermissionID FROM [dbo].[RolePermission] WHERE RoleID = 1);

-- 3. Manager 역할(RoleID=2): 모든 권한
INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
SELECT 2, PermissionID FROM [dbo].[Permission]
WHERE Module = N'Withdrawal'
  AND PermissionID NOT IN (SELECT PermissionID FROM [dbo].[RolePermission] WHERE RoleID = 2);

-- 4. Viewer 역할(RoleID=3): READ만
INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
SELECT 3, PermissionID FROM [dbo].[Permission]
WHERE Module = N'Withdrawal' AND Action = N'READ'
  AND PermissionID NOT IN (SELECT PermissionID FROM [dbo].[RolePermission] WHERE RoleID = 3);

-- 확인
SELECT p.PermissionID, p.Module, p.Action, p.Name, p.Description
FROM [dbo].[Permission] p
WHERE p.Module = N'Withdrawal'
ORDER BY p.PermissionID;
