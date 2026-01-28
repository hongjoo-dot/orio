-- =====================================================
-- Promotion 모듈 권한 추가 (6개)
-- 행사 관리 기능에 필요한 권한 등록
-- =====================================================

-- 1. Promotion 권한 삽입
INSERT INTO [dbo].[Permission] (Module, Action, Name, Description) VALUES
(N'Promotion', N'READ', N'행사 조회', N'행사 목록 및 상세 조회'),
(N'Promotion', N'CREATE', N'행사 등록', N'새 행사 등록'),
(N'Promotion', N'UPDATE', N'행사 수정', N'행사 정보 수정'),
(N'Promotion', N'DELETE', N'행사 삭제', N'행사 삭제'),
(N'Promotion', N'EXPORT', N'행사 엑셀 다운로드', N'행사 데이터 엑셀 내보내기'),
(N'Promotion', N'UPLOAD', N'행사 엑셀 업로드', N'행사 데이터 일괄 업로드');

-- 2. Admin 역할 (RoleID=1): 모든 Promotion 권한
INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
SELECT 1, PermissionID FROM [dbo].[Permission]
WHERE Module = N'Promotion';

-- 3. Manager 역할 (RoleID=2): 모든 Promotion 권한
INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
SELECT 2, PermissionID FROM [dbo].[Permission]
WHERE Module = N'Promotion';

-- 4. Viewer 역할 (RoleID=3): READ 권한만
INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
SELECT 3, PermissionID FROM [dbo].[Permission]
WHERE Module = N'Promotion' AND Action = N'READ';

PRINT N'Promotion 모듈 권한 6개 추가 완료';
