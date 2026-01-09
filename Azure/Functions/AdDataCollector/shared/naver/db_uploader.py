"""
네이버 광고 데이터 DB 업로드 모듈
"""

import pandas as pd
from ..database import get_db_connection


class NaverDBUploader:
    """네이버 광고 데이터를 Azure SQL DB에 업로드"""

    def upload_data(self, df: pd.DataFrame):
        """
        데이터 업로드 (AdDataNaver)
        MERGE 문을 사용하여 중복 방지 (Date + AdID + KeywordID + Device 기준)
        """
        if df.empty:
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 임시 테이블 생성
            cursor.execute("""
                CREATE TABLE #TempAdDataNaver (
                    [Date] [date],
                    [CampaignID] [nvarchar](50),
                    [CampaignName] [nvarchar](200),
                    [AdGroupID] [nvarchar](50),
                    [AdGroupName] [nvarchar](200),
                    [KeywordID] [nvarchar](50),
                    [Keyword] [nvarchar](200),
                    [AdID] [nvarchar](50),
                    [AdName] [nvarchar](200),
                    [Device] [nvarchar](20),
                    [Impressions] [int],
                    [Clicks] [int],
                    [Conversions] [int],
                    [ConversionValue] [float]
                )
            """)

            # 데이터 삽입
            data_to_insert = []
            for _, row in df.iterrows():
                data_to_insert.append((
                    row['Date'], row['CampaignID'], row['CampaignName'],
                    row['AdGroupID'], row['AdGroupName'],
                    row['KeywordID'], row['Keyword'],
                    row['AdID'], row['AdName'],
                    row['Device'], row['Impressions'], row['Clicks'],
                    row['Conversions'], row['ConversionValue']
                ))

            insert_query = "INSERT INTO #TempAdDataNaver VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            cursor.executemany(insert_query, data_to_insert)

            # MERGE 실행
            merge_query = """
                MERGE INTO [dbo].[AdDataNaver] AS target
                USING #TempAdDataNaver AS source
                ON target.Date = source.Date 
                   AND target.AdID = source.AdID 
                   AND target.KeywordID = source.KeywordID 
                   AND target.Device = source.Device
                
                WHEN MATCHED THEN
                    UPDATE SET
                        CampaignID = source.CampaignID,
                        CampaignName = source.CampaignName,
                        AdGroupID = source.AdGroupID,
                        AdGroupName = source.AdGroupName,
                        Keyword = source.Keyword,
                        AdName = source.AdName,
                        Impressions = source.Impressions,
                        Clicks = source.Clicks,
                        Conversions = source.Conversions,
                        ConversionValue = source.ConversionValue,
                        UpdatedDate = GETDATE()
                        
                WHEN NOT MATCHED THEN
                    INSERT (
                        Date, CampaignID, CampaignName, AdGroupID, AdGroupName,
                        KeywordID, Keyword, AdID, AdName, Device,
                        Impressions, Clicks, Conversions, ConversionValue,
                        CollectedDate, UpdatedDate
                    )
                    VALUES (
                        source.Date, source.CampaignID, source.CampaignName, 
                        source.AdGroupID, source.AdGroupName,
                        source.KeywordID, source.Keyword, source.AdID, source.AdName, source.Device,
                        source.Impressions, source.Clicks, source.Conversions, source.ConversionValue,
                        GETDATE(), GETDATE()
                    );
            """
            cursor.execute(merge_query)
            conn.commit()
            print(f"[DB] AdDataNaver {len(df)}건 업로드 완료")

        except Exception as e:
            print(f"[ERROR] AdDataNaver 업로드 실패: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def get_missing_dates(self, lookback_days: int = 7) -> list:
        """최근 N일 중 데이터가 없는 날짜 조회"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT Date
                FROM [dbo].[AdDataNaver]
                WHERE Date >= DATEADD(day, ?, CAST(GETDATE() AS DATE))
            """, -lookback_days)
            
            existing_dates = {row[0].strftime('%Y-%m-%d') for row in cursor.fetchall()}
            
            from datetime import datetime, timedelta
            today = datetime.now().date()
            missing_dates = []
            
            for i in range(1, lookback_days + 1):
                check_date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
                if check_date not in existing_dates:
                    missing_dates.append(check_date)
            
            return sorted(missing_dates)
            
        finally:
            cursor.close()
            conn.close()
