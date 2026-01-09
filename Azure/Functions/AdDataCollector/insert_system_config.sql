-- ================================================
-- AdDataCollector SystemConfig 설정값 추가 스크립트
-- ================================================

-- 1. Meta Ads 계정 정보 (JSON 형식)
INSERT INTO [dbo].[SystemConfig]
(Category, ConfigKey, ConfigValue, DataType, Description, IsActive, CreatedDate, UpdatedDate, UpdatedBy)
VALUES
(
    'MetaAdAPI',
    'AD_ACCOUNTS',
    '[{"id": "act_794495572822292", "name": "main"}, {"id": "act_1441231817023387", "name": "29cm"}]',
    'json',
    N'Meta 광고 계정 목록 (id: 계정ID, name: 표시명)',
    1,
    GETDATE(),
    GETDATE(),
    'SYSTEM'
);

-- 2. 환율 (USD → KRW)
INSERT INTO [dbo].[SystemConfig]
(Category, ConfigKey, ConfigValue, DataType, Description, IsActive, CreatedDate, UpdatedDate, UpdatedBy)
VALUES
(
    'Common',
    'USD_TO_KRW_RATE',
    '1400',
    'int',
    N'환율: USD → KRW 환산율 (Meta Ads 데이터 원화 변환용)',
    1,
    GETDATE(),
    GETDATE(),
    'SYSTEM'
);

-- 3. Naver Ads 대상 캠페인 필터 (선택 사항)
INSERT INTO [dbo].[SystemConfig]
(Category, ConfigKey, ConfigValue, DataType, Description, IsActive, CreatedDate, UpdatedDate, UpdatedBy)
VALUES
(
    'NaverAdAPI',
    'TARGET_CAMPAIGN_NAME',
    N'브랜드검색_섬네일형MO',
    'string',
    N'Naver 광고 수집 시 필터링할 캠페인명 (해당 캠페인만 수집)',
    1,
    GETDATE(),
    GETDATE(),
    'SYSTEM'
);

-- 확인 쿼리
SELECT
    ConfigID,
    Category,
    ConfigKey,
    ConfigValue,
    DataType,
    Description,
    IsActive
FROM [dbo].[SystemConfig]
WHERE Category IN ('MetaAdAPI', 'NaverAdAPI', 'Common')
ORDER BY Category, ConfigKey;
