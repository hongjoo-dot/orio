-- =====================================================
-- 누락된 권한 3개 추가
-- =====================================================

INSERT INTO [dbo].[Permission] (Module, Action, Name, Description) VALUES
('Sales', 'UPLOAD', '매출 엑셀 업로드', '매출 데이터 일괄 업로드'),
('Target', 'EXPORT', '목표 엑셀 다운로드', '목표 데이터 엑셀 내보내기'),
('Admin', 'PASSWORD_RESET', '비밀번호 초기화', '사용자 비밀번호 초기화');

-- Admin 역할에 새 권한 추가
INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
SELECT 1, PermissionID FROM [dbo].[Permission]
WHERE (Module = 'Sales' AND Action = 'UPLOAD')
   OR (Module = 'Target' AND Action = 'EXPORT')
   OR (Module = 'Admin' AND Action = 'PASSWORD_RESET');

-- Manager 역할에 Sales UPLOAD, Target EXPORT 추가 (Admin 제외)
INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
SELECT 2, PermissionID FROM [dbo].[Permission]
WHERE (Module = 'Sales' AND Action = 'UPLOAD')
   OR (Module = 'Target' AND Action = 'EXPORT');

PRINT '누락된 권한 3개 추가 완료';
