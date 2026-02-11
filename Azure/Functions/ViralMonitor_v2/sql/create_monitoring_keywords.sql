-- =====================================================
-- ViralKeywords 테이블 생성
-- 바이럴 모니터링 키워드 관리 (search / filter / exclude)
-- =====================================================

CREATE TABLE dbo.ViralKeywords (
    KeywordID    INT IDENTITY(1,1) PRIMARY KEY,
    BrandName    NVARCHAR(50)  NOT NULL,      -- '스크럽대디', '프로그'
    KeywordType  NVARCHAR(20)  NOT NULL,      -- 'search', 'filter', 'exclude'
    Keyword      NVARCHAR(100) NOT NULL,
    IsActive     BIT DEFAULT 1,
    Description  NVARCHAR(200) NULL,
    CreatedDate  DATETIME DEFAULT GETDATE(),
    UpdatedDate  DATETIME DEFAULT GETDATE(),
    UpdatedBy    NVARCHAR(50) DEFAULT 'SYSTEM'
);

-- 인덱스: 브랜드 + 타입 + 활성 상태 조회 최적화
CREATE NONCLUSTERED INDEX IX_ViralKeywords_Brand_Type
ON dbo.ViralKeywords (BrandName, KeywordType, IsActive)
INCLUDE (Keyword);


-- =====================================================
-- 초기 데이터 INSERT: 스크럽대디
-- =====================================================

-- 스크럽대디 - search (API 검색 키워드)
INSERT INTO dbo.ViralKeywords (BrandName, KeywordType, Keyword, Description) VALUES
(N'스크럽대디', 'search', N'스크럽대디',    N'브랜드명 (기본)'),
(N'스크럽대디', 'search', N'스크럽 대디',   N'브랜드명 (띄어쓰기)'),
(N'스크럽대디', 'search', N'스크랩대디',    N'브랜드명 (오타)'),
(N'스크럽대디', 'search', N'스크럽daddy',   N'브랜드명 (혼합)'),
(N'스크럽대디', 'search', N'Scrub Daddy',  N'브랜드명 (영문)'),
(N'스크럽대디', 'search', N'ScrubDaddy',   N'브랜드명 (영문 붙여쓰기)'),
(N'스크럽대디', 'search', N'scrubdaddy',   N'브랜드명 (영문 소문자)');


-- =====================================================
-- 초기 데이터 INSERT: 프로그
-- =====================================================

-- 프로그 - search (1단계: API 검색 키워드)
INSERT INTO dbo.ViralKeywords (BrandName, KeywordType, Keyword, Description) VALUES
(N'프로그', 'search', N'프로그',   N'브랜드명 (기본)'),
(N'프로그', 'search', N'FROG',    N'브랜드명 (영문 대문자)'),
(N'프로그', 'search', N'Frog',    N'브랜드명 (영문)'),
(N'프로그', 'search', N'frog',    N'브랜드명 (영문 소문자)');

-- 프로그 - filter (2단계: 제품 키워드 필터링)
INSERT INTO dbo.ViralKeywords (BrandName, KeywordType, Keyword, Description) VALUES
(N'프로그', 'filter', N'고무장갑',    N'제품 카테고리'),
(N'프로그', 'filter', N'수세미',     N'제품 카테고리'),
(N'프로그', 'filter', N'설거지',     N'사용 용도'),
(N'프로그', 'filter', N'청소',      N'사용 용도'),
(N'프로그', 'filter', N'주방',      N'사용 장소'),
(N'프로그', 'filter', N'세제',      N'제품 카테고리'),
(N'프로그', 'filter', N'칫솔',      N'제품 카테고리'),
(N'프로그', 'filter', N'행주',      N'제품 카테고리'),
(N'프로그', 'filter', N'니트릴장갑',  N'제품 카테고리'),
(N'프로그', 'filter', N'지퍼백',     N'제품 카테고리'),
(N'프로그', 'filter', N'매직블럭',   N'제품 카테고리'),
(N'프로그', 'filter', N'핫딜',      N'구매 관련'),
(N'프로그', 'filter', N'특가',      N'구매 관련'),
(N'프로그', 'filter', N'쿠팡',      N'구매 채널');


-- =====================================================
-- 확인 쿼리
-- =====================================================

-- 전체 데이터 확인
SELECT BrandName, KeywordType, COUNT(*) AS KeywordCount
FROM dbo.ViralKeywords
WHERE IsActive = 1
GROUP BY BrandName, KeywordType
ORDER BY BrandName, KeywordType;

-- 상세 목록 확인
SELECT KeywordID, BrandName, KeywordType, Keyword, IsActive, Description
FROM dbo.ViralKeywords
ORDER BY BrandName, KeywordType, KeywordID;