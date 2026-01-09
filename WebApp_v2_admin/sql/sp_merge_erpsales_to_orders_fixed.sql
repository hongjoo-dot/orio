-- =============================================
-- Stored Procedure: sp_MergeERPSalesToOrders (수정본)
-- 설명: ERPSales 데이터를 OrdersRealtime으로 동기화 (MERGE 방식)
-- 필터: Channel.LiveSource = 'ERP'
-- 중복 체크: SourceOrderID (ERPIDX)
-- 수정: OUTPUT 절을 사용하여 정확한 INSERT/UPDATE 카운트 추적
-- =============================================

CREATE OR ALTER PROCEDURE [dbo].[sp_MergeERPSalesToOrders]
    @StartDate DATE = NULL,
    @EndDate DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @InsertCount INT = 0;
    DECLARE @UpdateCount INT = 0;
    DECLARE @ErrorCount INT = 0;

    -- MERGE 결과를 저장할 임시 테이블
    DECLARE @MergeOutput TABLE (
        ActionType NVARCHAR(10)
    );

    BEGIN TRY
        BEGIN TRANSACTION;

        -- MERGE 실행 with OUTPUT
        MERGE INTO [dbo].[OrdersRealtime] AS Target
        USING (
            SELECT
                'ERP' AS SourceChannel,
                erp.ERPIDX AS SourceOrderID,
                ch.ContractType AS ContractType,
                erp.DATE AS OrderDate,
                erp.ChannelID,
                erp.ProductID,
                erp.ChannelDetailName AS CustomerName,
                CAST(ROUND(erp.Quantity, 0) AS INT) AS OrderQuantity,
                erp.UnitPrice AS OrderPrice,
                erp.TaxableAmount AS OrderAmount,
                'balanced' AS OrderStatus,
                erp.CollectedDate,
                GETDATE() AS UpdatedDate,
                erp.BrandID,
                erp.DATE AS ShippedDate,
                NULL AS SabangnetIDX
            FROM [dbo].[ERPSales] erp
            INNER JOIN [dbo].[Channel] ch ON erp.ChannelID = ch.ChannelID
            WHERE ch.LiveSource IN ('ERP', '2P')
                AND erp.ERPIDX IS NOT NULL
                AND (@StartDate IS NULL OR erp.DATE >= @StartDate)
                AND (@EndDate IS NULL OR erp.DATE <= @EndDate)
        ) AS Source
        ON Target.SourceChannel = Source.SourceChannel
            AND Target.SourceOrderID = Source.SourceOrderID

        -- 매칭되면 UPDATE
        WHEN MATCHED THEN
            UPDATE SET
                Target.ContractType = Source.ContractType,
                Target.OrderDate = Source.OrderDate,
                Target.ChannelID = Source.ChannelID,
                Target.ProductID = Source.ProductID,
                Target.CustomerName = Source.CustomerName,
                Target.OrderQuantity = Source.OrderQuantity,
                Target.OrderPrice = Source.OrderPrice,
                Target.OrderAmount = Source.OrderAmount,
                Target.OrderStatus = Source.OrderStatus,
                Target.CollectedDate = Source.CollectedDate,
                Target.UpdatedDate = Source.UpdatedDate,
                Target.BrandID = Source.BrandID,
                Target.ShippedDate = Source.ShippedDate

        -- 매칭 안 되면 INSERT
        WHEN NOT MATCHED BY TARGET THEN
            INSERT (
                SourceChannel,
                SourceOrderID,
                ContractType,
                OrderDate,
                ChannelID,
                ProductID,
                CustomerName,
                OrderQuantity,
                OrderPrice,
                OrderAmount,
                OrderStatus,
                CollectedDate,
                UpdatedDate,
                BrandID,
                ShippedDate,
                SabangnetIDX
            )
            VALUES (
                Source.SourceChannel,
                Source.SourceOrderID,
                Source.ContractType,
                Source.OrderDate,
                Source.ChannelID,
                Source.ProductID,
                Source.CustomerName,
                Source.OrderQuantity,
                Source.OrderPrice,
                Source.OrderAmount,
                Source.OrderStatus,
                Source.CollectedDate,
                Source.UpdatedDate,
                Source.BrandID,
                Source.ShippedDate,
                Source.SabangnetIDX
            )

        -- OUTPUT: INSERT는 'INSERT', UPDATE는 'UPDATE' 반환
        OUTPUT $action INTO @MergeOutput;

        -- 카운트 계산
        SET @InsertCount = (SELECT COUNT(*) FROM @MergeOutput WHERE ActionType = 'INSERT');
        SET @UpdateCount = (SELECT COUNT(*) FROM @MergeOutput WHERE ActionType = 'UPDATE');

        COMMIT TRANSACTION;

        -- 결과 반환
        SELECT
            @InsertCount AS InsertCount,
            @UpdateCount AS UpdateCount,
            @ErrorCount AS ErrorCount,
            'Success' AS Status;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        -- 에러 정보 반환
        SELECT
            0 AS InsertCount,
            0 AS UpdateCount,
            1 AS ErrorCount,
            ERROR_MESSAGE() AS Status;
    END CATCH
END;
GO
