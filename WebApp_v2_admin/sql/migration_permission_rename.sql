-- ============================================================
-- Permission 테이블 Module 리네이밍
-- Target → Expected3PRegular (위탁 정기)
-- Irregular → Expected3PIrregular (위탁 비정기)
-- ============================================================

-- 1. 위탁 정기: Target → Expected3PRegular
UPDATE [dbo].[Permission]
SET Module = 'Expected3PRegular'
WHERE Module = 'Target';

-- 2. 위탁 비정기: Irregular → Expected3PIrregular
UPDATE [dbo].[Permission]
SET Module = 'Expected3PIrregular'
WHERE Module = 'Irregular';

-- 확인
SELECT PermissionID, Module, [Action], Name, Description
FROM [dbo].[Permission]
WHERE Module IN ('Expected3PRegular', 'Expected3PIrregular')
ORDER BY Module, [Action];
