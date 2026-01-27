-- =====================================================
-- Permission 한글 데이터 수정 (N prefix 추가)
-- 기존 데이터 삭제 후 재삽입
-- =====================================================

-- 1. 기존 데이터 삭제 (FK 제약으로 인해 순서 중요)
DELETE FROM [dbo].[UserPermission];
DELETE FROM [dbo].[RolePermission];
DELETE FROM [dbo].[Permission];

PRINT N'기존 권한 데이터 삭제 완료';

-- 2. Permission 데이터 재삽입 (N prefix 사용)
SET IDENTITY_INSERT [dbo].[Permission] ON;

INSERT INTO [dbo].[Permission] (PermissionID, Module, Action, Name, Description) VALUES
-- Product 모듈
(1, N'Product', N'READ', N'제품 조회', N'제품 목록 및 상세 조회'),
(2, N'Product', N'CREATE', N'제품 등록', N'새 제품 등록'),
(3, N'Product', N'UPDATE', N'제품 수정', N'제품 정보 수정'),
(4, N'Product', N'DELETE', N'제품 삭제', N'제품 삭제'),
(5, N'Product', N'EXPORT', N'제품 엑셀 다운로드', N'제품 데이터 엑셀 내보내기'),
(6, N'Product', N'UPLOAD', N'제품 엑셀 업로드', N'제품 데이터 일괄 업로드'),

-- Brand 모듈
(7, N'Brand', N'READ', N'브랜드 조회', N'브랜드 목록 및 상세 조회'),
(8, N'Brand', N'CREATE', N'브랜드 등록', N'새 브랜드 등록'),
(9, N'Brand', N'UPDATE', N'브랜드 수정', N'브랜드 정보 수정'),
(10, N'Brand', N'DELETE', N'브랜드 삭제', N'브랜드 삭제'),

-- Channel 모듈
(11, N'Channel', N'READ', N'채널 조회', N'채널 목록 및 상세 조회'),
(12, N'Channel', N'CREATE', N'채널 등록', N'새 채널 등록'),
(13, N'Channel', N'UPDATE', N'채널 수정', N'채널 정보 수정'),
(14, N'Channel', N'DELETE', N'채널 삭제', N'채널 삭제'),

-- BOM 모듈
(15, N'BOM', N'READ', N'BOM 조회', N'BOM 목록 및 상세 조회'),
(16, N'BOM', N'CREATE', N'BOM 등록', N'새 BOM 등록'),
(17, N'BOM', N'UPDATE', N'BOM 수정', N'BOM 정보 수정'),
(18, N'BOM', N'DELETE', N'BOM 삭제', N'BOM 삭제'),

-- Sales 모듈
(19, N'Sales', N'READ', N'매출 조회', N'매출 데이터 조회'),
(20, N'Sales', N'CREATE', N'매출 등록', N'매출 데이터 등록'),
(21, N'Sales', N'UPDATE', N'매출 수정', N'매출 데이터 수정'),
(22, N'Sales', N'DELETE', N'매출 삭제', N'매출 데이터 삭제'),
(23, N'Sales', N'SYNC', N'매출 동기화', N'ERP 매출 데이터 동기화'),
(24, N'Sales', N'EXPORT', N'매출 엑셀 다운로드', N'매출 데이터 엑셀 내보내기'),
(25, N'Sales', N'UPLOAD', N'매출 엑셀 업로드', N'매출 데이터 일괄 업로드'),

-- Target 모듈
(26, N'Target', N'READ', N'목표 조회', N'목표 데이터 조회'),
(27, N'Target', N'CREATE', N'목표 등록', N'목표 데이터 등록'),
(28, N'Target', N'UPDATE', N'목표 수정', N'목표 데이터 수정'),
(29, N'Target', N'DELETE', N'목표 삭제', N'목표 데이터 삭제'),
(30, N'Target', N'EXPORT', N'목표 엑셀 다운로드', N'목표 데이터 엑셀 내보내기'),
(31, N'Target', N'UPLOAD', N'목표 엑셀 업로드', N'목표 데이터 일괄 업로드'),

-- Admin 모듈 (관리자 전용)
(32, N'Admin', N'USER_READ', N'사용자 조회', N'사용자 목록 및 상세 조회'),
(33, N'Admin', N'USER_CREATE', N'사용자 등록', N'새 사용자 등록'),
(34, N'Admin', N'USER_UPDATE', N'사용자 수정', N'사용자 정보 수정'),
(35, N'Admin', N'USER_DELETE', N'사용자 삭제', N'사용자 삭제'),
(36, N'Admin', N'ROLE_MANAGE', N'역할/권한 관리', N'역할 및 권한 설정'),
(37, N'Admin', N'LOG_VIEW', N'활동 로그 조회', N'시스템 활동 이력 조회'),
(38, N'Admin', N'PASSWORD_RESET', N'비밀번호 초기화', N'사용자 비밀번호 초기화');

SET IDENTITY_INSERT [dbo].[Permission] OFF;

PRINT N'Permission 데이터 삽입 완료 (38개 권한)';

-- 3. 역할별 권한 재할당

-- Admin 역할 (RoleID=1): 모든 권한
INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
SELECT 1, PermissionID FROM [dbo].[Permission];

PRINT N'Admin 역할: 모든 권한 할당 완료';

-- Manager 역할 (RoleID=2): Admin 모듈 제외
INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
SELECT 2, PermissionID FROM [dbo].[Permission] WHERE Module != N'Admin';

PRINT N'Manager 역할: Admin 제외 권한 할당 완료';

-- Viewer 역할 (RoleID=3): READ 권한만
INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID)
SELECT 3, PermissionID FROM [dbo].[Permission] WHERE Action = N'READ';

PRINT N'Viewer 역할: 조회 권한만 할당 완료';

-- 확인
SELECT PermissionID, Module, Action, Name, Description FROM [dbo].[Permission] ORDER BY PermissionID;

PRINT N'====================================';
PRINT N'권한 데이터 수정 완료!';
PRINT N'====================================';
