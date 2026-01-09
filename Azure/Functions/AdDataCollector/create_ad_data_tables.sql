-- Meta Ads Data Tables (Updated to match legacy Google Sheets structure)

-- 1. Daily Performance Data
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AdDataMeta')
BEGIN
    CREATE TABLE [dbo].[AdDataMeta](
        [Idx] [bigint] IDENTITY(1,1) NOT NULL,
        [AccountName] [nvarchar](50) NOT NULL,
        [Date] [date] NOT NULL,
        [CampaignID] [nvarchar](50) NULL,
        [CampaignName] [nvarchar](200) NULL,
        [AdSetID] [nvarchar](50) NULL,
        [AdSetName] [nvarchar](200) NULL,
        [AdID] [nvarchar](50) NOT NULL,
        [AdName] [nvarchar](200) NULL,
        
        -- Basic Metrics
        [Impressions] [int] DEFAULT 0,
        [Reach] [int] DEFAULT 0,
        [Frequency] [float] DEFAULT 0,
        [Clicks] [int] DEFAULT 0,
        [UniqueClicks] [int] DEFAULT 0,
        [CTR] [float] DEFAULT 0,
        [UniqueCTR] [float] DEFAULT 0,
        [Spend] [float] DEFAULT 0,
        [CPM] [float] DEFAULT 0,
        [CPC] [float] DEFAULT 0,
        
        -- Inline & Quality
        [InlineLinkClicks] [int] DEFAULT 0,
        [InlineLinkClickCTR] [float] DEFAULT 0,
        [CostPerInlineLinkClick] [float] DEFAULT 0,
        [QualityRanking] [nvarchar](50) NULL,
        [EngagementRateRanking] [nvarchar](50) NULL,
        [ConversionRateRanking] [nvarchar](50) NULL,
        
        -- Actions
        [LinkClicks] [int] DEFAULT 0,
        [OutboundClicks] [int] DEFAULT 0,
        [LandingPageViews] [int] DEFAULT 0,
        [CompleteRegistration] [int] DEFAULT 0,
        [AddToCart] [int] DEFAULT 0,
        [InitiateCheckout] [int] DEFAULT 0,
        [Purchase] [int] DEFAULT 0,
        [WebsitePurchase] [int] DEFAULT 0,
        
        -- Engagement Actions
        [PostEngagement] [int] DEFAULT 0,
        [PostReaction] [int] DEFAULT 0,
        [Comment] [int] DEFAULT 0,
        [VideoView] [int] DEFAULT 0,
        [PostSave] [int] DEFAULT 0,
        [PageEngagement] [int] DEFAULT 0,
        [PostClick] [int] DEFAULT 0,
        
        -- Values (USD)
        [PurchaseValue] [float] DEFAULT 0,
        [WebsitePurchaseValue] [float] DEFAULT 0,
        
        -- Calculated (USD) - Optional to store, but good for consistency
        [AOV] [float] DEFAULT 0,
        [CPA] [float] DEFAULT 0,
        [ROAS] [float] DEFAULT 0,
        [CVR] [float] DEFAULT 0,
        
        -- Rates
        [EngagementRate] [float] DEFAULT 0,
        [ReactionRate] [float] DEFAULT 0,
        [CommentRate] [float] DEFAULT 0,
        [VideoViewRate] [float] DEFAULT 0,
        [SaveRate] [float] DEFAULT 0,
        
        -- KRW Converted (Optional, can be calculated in View)
        [SpendKRW] [float] DEFAULT 0,
        [PurchaseValueKRW] [float] DEFAULT 0,
        [AOVKRW] [float] DEFAULT 0,
        [CPAKRW] [float] DEFAULT 0,
        
        -- Creative Info
        [CreativeID] [nvarchar](50) NULL,
        [AdTitle] [nvarchar](max) NULL,
        [AdBody] [nvarchar](max) NULL,
        [CTAType] [nvarchar](50) NULL,
        [LinkURL] [nvarchar](max) NULL,
        [ImageURL] [nvarchar](max) NULL,
        [VideoID] [nvarchar](50) NULL,
        [ThumbnailURL] [nvarchar](max) NULL,
        
        [CollectedDate] [datetime] DEFAULT GETDATE(),
        [UpdatedDate] [datetime] DEFAULT GETDATE(),
        
        CONSTRAINT [PK_AdDataMeta] PRIMARY KEY CLUSTERED ([Idx] ASC)
    );

    CREATE NONCLUSTERED INDEX [IX_AdDataMeta_Date_AdID] ON [dbo].[AdDataMeta]
    (
        [Date] ASC,
        [AdID] ASC
    );
END
GO

-- 2. Breakdown Data
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AdDataMetaBreakdown')
BEGIN
    CREATE TABLE [dbo].[AdDataMetaBreakdown](
        [Idx] [bigint] IDENTITY(1,1) NOT NULL,
        [AccountName] [nvarchar](50) NOT NULL,
        [Date] [date] NOT NULL,
        [CampaignID] [nvarchar](50) NULL,
        [CampaignName] [nvarchar](200) NULL,
        [AdSetID] [nvarchar](50) NULL,
        [AdSetName] [nvarchar](200) NULL,
        [AdID] [nvarchar](50) NOT NULL,
        [AdName] [nvarchar](200) NULL,
        
        [BreakdownType] [nvarchar](50) NOT NULL,
        [Age] [nvarchar](50) NULL,
        [Gender] [nvarchar](20) NULL,
        [PublisherPlatform] [nvarchar](50) NULL,
        [DevicePlatform] [nvarchar](50) NULL,
        [ImpressionDevice] [nvarchar](50) NULL,
        
        -- Metrics
        [Impressions] [int] DEFAULT 0,
        [Reach] [int] DEFAULT 0,
        [Frequency] [float] DEFAULT 0,
        [Clicks] [int] DEFAULT 0,
        [CTR] [float] DEFAULT 0,
        [Spend] [float] DEFAULT 0,
        [CPM] [float] DEFAULT 0,
        [CPC] [float] DEFAULT 0,
        
        [LandingPageViews] [int] DEFAULT 0,
        [AddToCart] [int] DEFAULT 0,
        [InitiateCheckout] [int] DEFAULT 0,
        [Purchase] [int] DEFAULT 0,
        [CompleteRegistration] [int] DEFAULT 0,
        [OutboundClicks] [int] DEFAULT 0,
        [LinkClicks] [int] DEFAULT 0,
        
        [PurchaseValue] [float] DEFAULT 0,
        
        -- Calculated
        [AOV] [float] DEFAULT 0,
        [CPA] [float] DEFAULT 0,
        [ROAS] [float] DEFAULT 0,
        [CVR] [float] DEFAULT 0,
        
        -- KRW
        [SpendKRW] [float] DEFAULT 0,
        [PurchaseValueKRW] [float] DEFAULT 0,
        [AOVKRW] [float] DEFAULT 0,
        [CPAKRW] [float] DEFAULT 0,
        
        [CollectedDate] [datetime] DEFAULT GETDATE(),
        [UpdatedDate] [datetime] DEFAULT GETDATE(),
        
        CONSTRAINT [PK_AdDataMetaBreakdown] PRIMARY KEY CLUSTERED ([Idx] ASC)
    );

    CREATE NONCLUSTERED INDEX [IX_AdDataMetaBreakdown_Merge] ON [dbo].[AdDataMetaBreakdown]
    (
        [Date] ASC,
        [AdID] ASC,
        [BreakdownType] ASC
    );
END
GO

-- 3. Naver Search Ads Data
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AdDataNaver')
BEGIN
    CREATE TABLE [dbo].[AdDataNaver](
        [Idx] [bigint] IDENTITY(1,1) NOT NULL,
        [Date] [date] NOT NULL,
        [CampaignID] [nvarchar](50) NULL,
        [CampaignName] [nvarchar](200) NULL,
        [AdGroupID] [nvarchar](50) NULL,
        [AdGroupName] [nvarchar](200) NULL,
        [KeywordID] [nvarchar](50) NULL,
        [Keyword] [nvarchar](200) NULL,
        [AdID] [nvarchar](50) NOT NULL,
        [AdName] [nvarchar](200) NULL,
        [Device] [nvarchar](20) NULL,
        
        -- Metrics
        [Impressions] [int] DEFAULT 0,
        [Clicks] [int] DEFAULT 0,
        [Conversions] [int] DEFAULT 0,
        [ConversionValue] [float] DEFAULT 0,
        
        [CollectedDate] [datetime] DEFAULT GETDATE(),
        [UpdatedDate] [datetime] DEFAULT GETDATE(),
        
        CONSTRAINT [PK_AdDataNaver] PRIMARY KEY CLUSTERED ([Idx] ASC)
    );

    CREATE NONCLUSTERED INDEX [IX_AdDataNaver_Date_AdID] ON [dbo].[AdDataNaver]
    (
        [Date] ASC,
        [AdID] ASC,
        [KeywordID] ASC,
        [Device] ASC
    );
END
GO
