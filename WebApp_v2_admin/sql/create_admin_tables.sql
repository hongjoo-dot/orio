-- ================================================
-- Orio ERP Admin 기능용 테이블 생성 스크립트
-- 실행 순서대로 실행해 주세요
-- ================================================

-- 1. Role 테이블 (역할 정의)
CREATE TABLE [dbo].[Role] (
    RoleID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(50) NOT NULL UNIQUE,           -- 'Admin', 'Manager', 'Viewer'
    Description NVARCHAR(255),
    CreatedDate DATETIME DEFAULT GETDATE()
);

-- 기본 역할 추가
INSERT INTO [dbo].[Role] (Name, Description) VALUES 
    ('Admin', N'모든 권한 - 계정 관리, 권한 부여, 모든 CRUD'),
    ('Manager', N'관리자 권한 - 추후 권한 정립'),
    ('Viewer', N'조회 전용 - 검색, 필터, 조회만 가능');
GO

-- 2. User 테이블 (사용자 정보)
CREATE TABLE [dbo].[User] (
    UserID INT IDENTITY(1,1) PRIMARY KEY,
    Email NVARCHAR(255) NOT NULL UNIQUE,        -- 로그인 ID
    PasswordHash NVARCHAR(255) NOT NULL,        -- bcrypt 해시된 비밀번호
    Name NVARCHAR(100) NOT NULL,                -- 표시 이름
    IsActive BIT DEFAULT 1,                     -- 활성화 여부
    CreatedDate DATETIME DEFAULT GETDATE(),
    LastLoginDate DATETIME NULL,
    CreatedBy INT NULL                          -- 생성한 관리자 (FK → User)
);
GO

-- 3. UserRole 테이블 (사용자-역할 매핑)
CREATE TABLE [dbo].[UserRole] (
    UserRoleID INT IDENTITY(1,1) PRIMARY KEY,
    UserID INT NOT NULL,
    RoleID INT NOT NULL,
    AssignedDate DATETIME DEFAULT GETDATE(),
    AssignedBy INT NULL,                        -- 권한 부여한 관리자
    FOREIGN KEY (UserID) REFERENCES [dbo].[User](UserID) ON DELETE CASCADE,
    FOREIGN KEY (RoleID) REFERENCES [dbo].[Role](RoleID),
    FOREIGN KEY (AssignedBy) REFERENCES [dbo].[User](UserID),
    UNIQUE (UserID, RoleID)                     -- 중복 역할 방지
);
GO

-- 4. ActivityLog 테이블 (행동 이력)
CREATE TABLE [dbo].[ActivityLog] (
    LogID BIGINT IDENTITY(1,1) PRIMARY KEY,
    UserID INT NOT NULL,
    ActionType NVARCHAR(50) NOT NULL,           -- 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'LOGIN_FAILED'
    TargetTable NVARCHAR(100) NULL,             -- 대상 테이블명
    TargetID NVARCHAR(50) NULL,                 -- 대상 레코드 ID
    Details NVARCHAR(MAX) NULL,                 -- JSON 형태의 상세 정보
    IPAddress NVARCHAR(45) NULL,                -- 클라이언트 IP
    CreatedDate DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (UserID) REFERENCES [dbo].[User](UserID)
);
GO

-- 5. 인덱스 생성 (성능 최적화)
CREATE INDEX IX_ActivityLog_UserID ON [dbo].[ActivityLog](UserID);
CREATE INDEX IX_ActivityLog_ActionType ON [dbo].[ActivityLog](ActionType);
CREATE INDEX IX_ActivityLog_CreatedDate ON [dbo].[ActivityLog](CreatedDate DESC);
CREATE INDEX IX_User_Email ON [dbo].[User](Email);
GO

-- ================================================
-- 초기 Admin 계정 생성
-- 비밀번호: hongjoo (bcrypt 해시)
-- 해시는 Python에서 생성됨: $2b$12$... 형태
-- 아래 해시는 'hongjoo' 비밀번호의 bcrypt 해시입니다
-- ================================================
INSERT INTO [dbo].[User] (Email, PasswordHash, Name, IsActive, CreatedBy)
VALUES (
    N'hongjoo@orio.co.kr',
    N'$2b$12$Bhzh.zn1uY.LzAsVLlebue0fNijRQrd.knbDtCC///11.HZZRp6X32',  -- 'hongjoo'의 bcrypt 해시
    N'신홍주',
    1,
    NULL  -- 최초 관리자는 CreatedBy 없음
);
GO

-- Admin 역할 할당
INSERT INTO [dbo].[UserRole] (UserID, RoleID, AssignedBy)
VALUES (1, 1, NULL);  -- UserID=1 (hongjoo), RoleID=1 (Admin)
GO

-- 확인 쿼리
SELECT u.UserID, u.Email, u.Name, r.Name AS RoleName
FROM [dbo].[User] u
JOIN [dbo].[UserRole] ur ON u.UserID = ur.UserID
JOIN [dbo].[Role] r ON ur.RoleID = r.RoleID;
