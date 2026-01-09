"""
Meta Ads 데이터 DB 업로드 모듈 (Updated Schema)
"""

import pandas as pd
import pyodbc
from ..database import get_db_connection

class MetaDBUploader:
    """Meta Ads 데이터를 Azure SQL DB에 업로드"""

    def upload_daily_data(self, df: pd.DataFrame):
        """일별 성과 데이터 업로드 (AdDataMeta)"""
        if df.empty:
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 임시 테이블 생성 (스키마 확장됨)
            cursor.execute("""
                CREATE TABLE #TempAdDataMeta (
                    [AccountName] [nvarchar](50), [Date] [date],
                    [CampaignID] [nvarchar](50), [CampaignName] [nvarchar](200),
                    [AdSetID] [nvarchar](50), [AdSetName] [nvarchar](200),
                    [AdID] [nvarchar](50), [AdName] [nvarchar](200),
                    [Impressions] [int], [Reach] [int], [Frequency] [float],
                    [Clicks] [int], [UniqueClicks] [int], [CTR] [float], [UniqueCTR] [float],
                    [Spend] [float], [CPM] [float], [CPC] [float],
                    [InlineLinkClicks] [int], [InlineLinkClickCTR] [float], [CostPerInlineLinkClick] [float],
                    [QualityRanking] [nvarchar](50), [EngagementRateRanking] [nvarchar](50), [ConversionRateRanking] [nvarchar](50),
                    [LinkClicks] [int], [OutboundClicks] [int], [LandingPageViews] [int],
                    [CompleteRegistration] [int], [AddToCart] [int], [InitiateCheckout] [int],
                    [Purchase] [int], [WebsitePurchase] [int],
                    [PostEngagement] [int], [PostReaction] [int], [Comment] [int],
                    [VideoView] [int], [PostSave] [int], [PageEngagement] [int], [PostClick] [int],
                    [PurchaseValue] [float], [WebsitePurchaseValue] [float],
                    [AOV] [float], [CPA] [float], [ROAS] [float], [CVR] [float],
                    [EngagementRate] [float], [ReactionRate] [float], [CommentRate] [float],
                    [VideoViewRate] [float], [SaveRate] [float],
                    [SpendKRW] [float], [PurchaseValueKRW] [float], [AOVKRW] [float], [CPAKRW] [float],
                    [CreativeID] [nvarchar](50), [AdTitle] [nvarchar](max), [AdBody] [nvarchar](max),
                    [CTAType] [nvarchar](50), [LinkURL] [nvarchar](max), [ImageURL] [nvarchar](max),
                    [VideoID] [nvarchar](50), [ThumbnailURL] [nvarchar](max), [PreviewURL] [nvarchar](max)
                )
            """)

            # 데이터 매핑 및 삽입
            data_to_insert = []
            for _, row in df.iterrows():
                data_to_insert.append((
                    row['AccountName'], row['Date'], row['CampaignID'], row['CampaignName'],
                    row['AdSetID'], row['AdSetName'], row['AdID'], row['AdName'],
                    row['Impressions'], row['Reach'], row['Frequency'],
                    row['Clicks'], row['UniqueClicks'], row['CTR'], row['UniqueCTR'],
                    row['Spend'], row['CPM'], row['CPC'],
                    row['InlineLinkClicks'], row['InlineLinkClickCTR'], row['CostPerInlineLinkClick'],
                    row['QualityRanking'], row['EngagementRateRanking'], row['ConversionRateRanking'],
                    row['LinkClicks'], row['OutboundClicks'], row['LandingPageViews'],
                    row['CompleteRegistration'], row['AddToCart'], row['InitiateCheckout'],
                    row['Purchase'], row['WebsitePurchase'],
                    row['PostEngagement'], row['PostReaction'], row['Comment'],
                    row['VideoView'], row['PostSave'], row['PageEngagement'], row['PostClick'],
                    row['PurchaseValue'], row['WebsitePurchaseValue'],
                    row['AOV'], row['CPA'], row['ROAS'], row['CVR'],
                    row['EngagementRate'], row['ReactionRate'], row['CommentRate'],
                    row['VideoViewRate'], row['SaveRate'],
                    row['SpendKRW'], row['PurchaseValueKRW'], row['AOVKRW'], row['CPAKRW'],
                    row['CreativeID'], row['AdTitle'], row['AdBody'],
                    row['CTAType'], row['LinkURL'], row['ImageURL'],
                    row['VideoID'], row['ThumbnailURL'], row.get('PreviewURL')
                ))

            # 63개 컬럼
            placeholders = ','.join(['?'] * 63)
            insert_query = f"INSERT INTO #TempAdDataMeta VALUES ({placeholders})"
            cursor.executemany(insert_query, data_to_insert)

            # MERGE 실행
            merge_query = """
                MERGE INTO [dbo].[AdDataMeta] AS target
                USING #TempAdDataMeta AS source
                ON target.Date = source.Date AND target.AdID = source.AdID
                
                WHEN MATCHED THEN
                    UPDATE SET
                        AccountName = source.AccountName, CampaignID = source.CampaignID, CampaignName = source.CampaignName,
                        AdSetID = source.AdSetID, AdSetName = source.AdSetName, AdName = source.AdName,
                        Impressions = source.Impressions, Reach = source.Reach, Frequency = source.Frequency,
                        Clicks = source.Clicks, UniqueClicks = source.UniqueClicks, CTR = source.CTR, UniqueCTR = source.UniqueCTR,
                        Spend = source.Spend, CPM = source.CPM, CPC = source.CPC,
                        InlineLinkClicks = source.InlineLinkClicks, InlineLinkClickCTR = source.InlineLinkClickCTR, CostPerInlineLinkClick = source.CostPerInlineLinkClick,
                        QualityRanking = source.QualityRanking, EngagementRateRanking = source.EngagementRateRanking, ConversionRateRanking = source.ConversionRateRanking,
                        LinkClicks = source.LinkClicks, OutboundClicks = source.OutboundClicks, LandingPageViews = source.LandingPageViews,
                        CompleteRegistration = source.CompleteRegistration, AddToCart = source.AddToCart, InitiateCheckout = source.InitiateCheckout,
                        Purchase = source.Purchase, WebsitePurchase = source.WebsitePurchase,
                        PostEngagement = source.PostEngagement, PostReaction = source.PostReaction, Comment = source.Comment,
                        VideoView = source.VideoView, PostSave = source.PostSave, PageEngagement = source.PageEngagement, PostClick = source.PostClick,
                        PurchaseValue = source.PurchaseValue, WebsitePurchaseValue = source.WebsitePurchaseValue,
                        AOV = source.AOV, CPA = source.CPA, ROAS = source.ROAS, CVR = source.CVR,
                        EngagementRate = source.EngagementRate, ReactionRate = source.ReactionRate, CommentRate = source.CommentRate,
                        VideoViewRate = source.VideoViewRate, SaveRate = source.SaveRate,
                        SpendKRW = source.SpendKRW, PurchaseValueKRW = source.PurchaseValueKRW, AOVKRW = source.AOVKRW, CPAKRW = source.CPAKRW,
                        CreativeID = source.CreativeID, AdTitle = source.AdTitle, AdBody = source.AdBody,
                        CTAType = source.CTAType, LinkURL = source.LinkURL, ImageURL = source.ImageURL,
                        VideoID = source.VideoID, ThumbnailURL = source.ThumbnailURL, PreviewURL = source.PreviewURL,
                        UpdatedDate = GETDATE()
                        
                WHEN NOT MATCHED THEN
                    INSERT (
                        AccountName, Date, CampaignID, CampaignName, AdSetID, AdSetName, AdID, AdName,
                        Impressions, Reach, Frequency, Clicks, UniqueClicks, CTR, UniqueCTR, Spend, CPM, CPC,
                        InlineLinkClicks, InlineLinkClickCTR, CostPerInlineLinkClick,
                        QualityRanking, EngagementRateRanking, ConversionRateRanking,
                        LinkClicks, OutboundClicks, LandingPageViews, CompleteRegistration, AddToCart, InitiateCheckout,
                        Purchase, WebsitePurchase, PostEngagement, PostReaction, Comment, VideoView, PostSave, PageEngagement, PostClick,
                        PurchaseValue, WebsitePurchaseValue, AOV, CPA, ROAS, CVR,
                        EngagementRate, ReactionRate, CommentRate, VideoViewRate, SaveRate,
                        SpendKRW, PurchaseValueKRW, AOVKRW, CPAKRW,
                        CreativeID, AdTitle, AdBody, CTAType, LinkURL, ImageURL, VideoID, ThumbnailURL, PreviewURL,
                        CollectedDate, UpdatedDate
                    )
                    VALUES (
                        source.AccountName, source.Date, source.CampaignID, source.CampaignName, source.AdSetID, source.AdSetName, source.AdID, source.AdName,
                        source.Impressions, source.Reach, source.Frequency, source.Clicks, source.UniqueClicks, source.CTR, source.UniqueCTR, source.Spend, source.CPM, source.CPC,
                        source.InlineLinkClicks, source.InlineLinkClickCTR, source.CostPerInlineLinkClick,
                        source.QualityRanking, source.EngagementRateRanking, source.ConversionRateRanking,
                        source.LinkClicks, source.OutboundClicks, source.LandingPageViews, source.CompleteRegistration, source.AddToCart, source.InitiateCheckout,
                        source.Purchase, source.WebsitePurchase, source.PostEngagement, source.PostReaction, source.Comment, source.VideoView, source.PostSave, source.PageEngagement, source.PostClick,
                        source.PurchaseValue, source.WebsitePurchaseValue, source.AOV, source.CPA, source.ROAS, source.CVR,
                        source.EngagementRate, source.ReactionRate, source.CommentRate, source.VideoViewRate, source.SaveRate,
                        source.SpendKRW, source.PurchaseValueKRW, source.AOVKRW, source.CPAKRW,
                        source.CreativeID, source.AdTitle, source.AdBody, source.CTAType, source.LinkURL, source.ImageURL, source.VideoID, source.ThumbnailURL, source.PreviewURL,
                        GETDATE(), GETDATE()
                    );
            """
            cursor.execute(merge_query)
            conn.commit()
            print(f"[DB] AdDataMeta {len(df)}건 업로드 완료")

        except Exception as e:
            print(f"[ERROR] AdDataMeta 업로드 실패: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def upload_breakdown_data(self, df: pd.DataFrame):
        """Breakdown 데이터 업로드 (Updated Schema)"""
        if df.empty:
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                CREATE TABLE #TempAdDataMetaBreakdown (
                    [AccountName] [nvarchar](50), [Date] [date],
                    [CampaignID] [nvarchar](50), [CampaignName] [nvarchar](200),
                    [AdSetID] [nvarchar](50), [AdSetName] [nvarchar](200),
                    [AdID] [nvarchar](50), [AdName] [nvarchar](200),
                    [BreakdownType] [nvarchar](50),
                    [Age] [nvarchar](50), [Gender] [nvarchar](20),
                    [PublisherPlatform] [nvarchar](50), [DevicePlatform] [nvarchar](50), [ImpressionDevice] [nvarchar](50),
                    [Impressions] [int], [Reach] [int], [Frequency] [float],
                    [Clicks] [int], [CTR] [float], [Spend] [float], [CPM] [float], [CPC] [float],
                    [LandingPageViews] [int], [AddToCart] [int], [InitiateCheckout] [int],
                    [Purchase] [int], [CompleteRegistration] [int], [OutboundClicks] [int], [LinkClicks] [int],
                    [PurchaseValue] [float],
                    [AOV] [float], [CPA] [float], [ROAS] [float], [CVR] [float],
                    [SpendKRW] [float], [PurchaseValueKRW] [float], [AOVKRW] [float], [CPAKRW] [float]
                )
            """)

            data_to_insert = []
            for _, row in df.iterrows():
                data_to_insert.append((
                    row['AccountName'], row['Date'], row['CampaignID'], row['CampaignName'],
                    row['AdSetID'], row['AdSetName'], row['AdID'], row['AdName'],
                    row['BreakdownType'], row.get('Age'), row.get('Gender'),
                    row.get('PublisherPlatform'), row.get('DevicePlatform'), row.get('ImpressionDevice'),
                    row['Impressions'], row['Reach'], row['Frequency'],
                    row['Clicks'], row['CTR'], row['Spend'], row['CPM'], row['CPC'],
                    row['LandingPageViews'], row['AddToCart'], row['InitiateCheckout'],
                    row['Purchase'], row['CompleteRegistration'], row['OutboundClicks'], row['LinkClicks'],
                    row['PurchaseValue'],
                    row['AOV'], row['CPA'], row['ROAS'], row['CVR'],
                    row['SpendKRW'], row['PurchaseValueKRW'], row['AOVKRW'], row['CPAKRW']
                ))

            # 38개 컬럼
            placeholders = ','.join(['?'] * 38)
            insert_query = f"INSERT INTO #TempAdDataMetaBreakdown VALUES ({placeholders})"
            cursor.executemany(insert_query, data_to_insert)

            merge_query = """
                MERGE INTO [dbo].[AdDataMetaBreakdown] AS target
                USING #TempAdDataMetaBreakdown AS source
                ON target.Date = source.Date 
                   AND target.AdID = source.AdID 
                   AND target.BreakdownType = source.BreakdownType
                   AND ISNULL(target.Age, '') = ISNULL(source.Age, '')
                   AND ISNULL(target.Gender, '') = ISNULL(source.Gender, '')
                   AND ISNULL(target.PublisherPlatform, '') = ISNULL(source.PublisherPlatform, '')
                   AND ISNULL(target.DevicePlatform, '') = ISNULL(source.DevicePlatform, '')
                
                WHEN MATCHED THEN
                    UPDATE SET
                        AccountName = source.AccountName, CampaignID = source.CampaignID, CampaignName = source.CampaignName,
                        AdSetID = source.AdSetID, AdSetName = source.AdSetName, AdName = source.AdName,
                        Impressions = source.Impressions, Reach = source.Reach, Frequency = source.Frequency,
                        Clicks = source.Clicks, CTR = source.CTR, Spend = source.Spend, CPM = source.CPM, CPC = source.CPC,
                        LandingPageViews = source.LandingPageViews, AddToCart = source.AddToCart, InitiateCheckout = source.InitiateCheckout,
                        Purchase = source.Purchase, CompleteRegistration = source.CompleteRegistration,
                        OutboundClicks = source.OutboundClicks, LinkClicks = source.LinkClicks,
                        PurchaseValue = source.PurchaseValue,
                        AOV = source.AOV, CPA = source.CPA, ROAS = source.ROAS, CVR = source.CVR,
                        SpendKRW = source.SpendKRW, PurchaseValueKRW = source.PurchaseValueKRW, AOVKRW = source.AOVKRW, CPAKRW = source.CPAKRW,
                        UpdatedDate = GETDATE()
                        
                WHEN NOT MATCHED THEN
                    INSERT (
                        AccountName, Date, CampaignID, CampaignName, AdSetID, AdSetName, AdID, AdName,
                        BreakdownType, Age, Gender, PublisherPlatform, DevicePlatform, ImpressionDevice,
                        Impressions, Reach, Frequency, Clicks, CTR, Spend, CPM, CPC,
                        LandingPageViews, AddToCart, InitiateCheckout, Purchase, CompleteRegistration, OutboundClicks, LinkClicks,
                        PurchaseValue, AOV, CPA, ROAS, CVR, SpendKRW, PurchaseValueKRW, AOVKRW, CPAKRW,
                        CollectedDate, UpdatedDate
                    )
                    VALUES (
                        source.AccountName, source.Date, source.CampaignID, source.CampaignName, source.AdSetID, source.AdSetName, source.AdID, source.AdName,
                        source.BreakdownType, source.Age, source.Gender, source.PublisherPlatform, source.DevicePlatform, source.ImpressionDevice,
                        source.Impressions, source.Reach, source.Frequency, source.Clicks, source.CTR, source.Spend, source.CPM, source.CPC,
                        source.LandingPageViews, source.AddToCart, source.InitiateCheckout, source.Purchase, source.CompleteRegistration, source.OutboundClicks, source.LinkClicks,
                        source.PurchaseValue, source.AOV, source.CPA, source.ROAS, source.CVR, source.SpendKRW, source.PurchaseValueKRW, source.AOVKRW, source.CPAKRW,
                        GETDATE(), GETDATE()
                    );
            """
            cursor.execute(merge_query)
            conn.commit()
            print(f"[DB] AdDataMetaBreakdown {len(df)}건 업로드 완료")

        except Exception as e:
            print(f"[ERROR] AdDataMetaBreakdown 업로드 실패: {e}")
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
                FROM [dbo].[AdDataMeta]
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
