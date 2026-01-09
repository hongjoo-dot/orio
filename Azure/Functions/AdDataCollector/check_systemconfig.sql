-- SystemConfig 테이블 확인 쿼리
-- NaverAdAPI와 MetaAdAPI 설정 확인

SELECT
    ConfigID,
    Category,
    ConfigKey,
    ConfigValue,
    DataType,
    IsActive,
    Description
FROM [dbo].[SystemConfig]
WHERE Category IN ('NaverAdAPI', 'MetaAdAPI', 'Common')
ORDER BY Category, ConfigKey;
