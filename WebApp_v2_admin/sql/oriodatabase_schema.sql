-- DROP SCHEMA dbo;

CREATE SCHEMA dbo;
-- oriodatabase.dbo.AdDataMeta definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.AdDataMeta;

CREATE TABLE oriodatabase.dbo.AdDataMeta (
	Idx bigint IDENTITY(1,1) NOT NULL,
	AccountName nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	[Date] date NOT NULL,
	CampaignID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CampaignName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdSetID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdSetName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	AdName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Impressions int DEFAULT 0 NULL,
	Reach int DEFAULT 0 NULL,
	Frequency float DEFAULT 0 NULL,
	Clicks int DEFAULT 0 NULL,
	UniqueClicks int DEFAULT 0 NULL,
	CTR float DEFAULT 0 NULL,
	UniqueCTR float DEFAULT 0 NULL,
	Spend float DEFAULT 0 NULL,
	CPM float DEFAULT 0 NULL,
	CPC float DEFAULT 0 NULL,
	InlineLinkClicks int DEFAULT 0 NULL,
	InlineLinkClickCTR float DEFAULT 0 NULL,
	CostPerInlineLinkClick float DEFAULT 0 NULL,
	QualityRanking nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	EngagementRateRanking nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ConversionRateRanking nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	LinkClicks int DEFAULT 0 NULL,
	OutboundClicks int DEFAULT 0 NULL,
	LandingPageViews int DEFAULT 0 NULL,
	CompleteRegistration int DEFAULT 0 NULL,
	AddToCart int DEFAULT 0 NULL,
	InitiateCheckout int DEFAULT 0 NULL,
	Purchase int DEFAULT 0 NULL,
	WebsitePurchase int DEFAULT 0 NULL,
	PostEngagement int DEFAULT 0 NULL,
	PostReaction int DEFAULT 0 NULL,
	Comment int DEFAULT 0 NULL,
	VideoView int DEFAULT 0 NULL,
	PostSave int DEFAULT 0 NULL,
	PageEngagement int DEFAULT 0 NULL,
	PostClick int DEFAULT 0 NULL,
	PurchaseValue float DEFAULT 0 NULL,
	WebsitePurchaseValue float DEFAULT 0 NULL,
	AOV float DEFAULT 0 NULL,
	CPA float DEFAULT 0 NULL,
	ROAS float DEFAULT 0 NULL,
	CVR float DEFAULT 0 NULL,
	EngagementRate float DEFAULT 0 NULL,
	ReactionRate float DEFAULT 0 NULL,
	CommentRate float DEFAULT 0 NULL,
	VideoViewRate float DEFAULT 0 NULL,
	SaveRate float DEFAULT 0 NULL,
	SpendKRW float DEFAULT 0 NULL,
	PurchaseValueKRW float DEFAULT 0 NULL,
	AOVKRW float DEFAULT 0 NULL,
	CPAKRW float DEFAULT 0 NULL,
	CreativeID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdTitle nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdBody nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CTAType nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	LinkURL nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ImageURL nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	VideoID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ThumbnailURL nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CollectedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	PreviewURL nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK_AdDataMeta PRIMARY KEY (Idx)
);
 CREATE NONCLUSTERED INDEX IX_AdDataMeta_AccountName_Date ON oriodatabase.dbo.AdDataMeta (  AccountName ASC  , Date ASC  )  
	 INCLUDE ( Purchase , PurchaseValue , Spend , SpendKRW ) 
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_AdDataMeta_Date_AdID ON oriodatabase.dbo.AdDataMeta (  Date ASC  , AdID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.AdDataMetaBreakdown definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.AdDataMetaBreakdown;

CREATE TABLE oriodatabase.dbo.AdDataMetaBreakdown (
	Idx bigint IDENTITY(1,1) NOT NULL,
	AccountName nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	[Date] date NOT NULL,
	CampaignID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CampaignName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdSetID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdSetName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	AdName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	BreakdownType nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Age nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Gender nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PublisherPlatform nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	DevicePlatform nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ImpressionDevice nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Impressions int DEFAULT 0 NULL,
	Reach int DEFAULT 0 NULL,
	Frequency float DEFAULT 0 NULL,
	Clicks int DEFAULT 0 NULL,
	CTR float DEFAULT 0 NULL,
	Spend float DEFAULT 0 NULL,
	CPM float DEFAULT 0 NULL,
	CPC float DEFAULT 0 NULL,
	LandingPageViews int DEFAULT 0 NULL,
	AddToCart int DEFAULT 0 NULL,
	InitiateCheckout int DEFAULT 0 NULL,
	Purchase int DEFAULT 0 NULL,
	CompleteRegistration int DEFAULT 0 NULL,
	OutboundClicks int DEFAULT 0 NULL,
	LinkClicks int DEFAULT 0 NULL,
	PurchaseValue float DEFAULT 0 NULL,
	AOV float DEFAULT 0 NULL,
	CPA float DEFAULT 0 NULL,
	ROAS float DEFAULT 0 NULL,
	CVR float DEFAULT 0 NULL,
	SpendKRW float DEFAULT 0 NULL,
	PurchaseValueKRW float DEFAULT 0 NULL,
	AOVKRW float DEFAULT 0 NULL,
	CPAKRW float DEFAULT 0 NULL,
	CollectedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK_AdDataMetaBreakdown PRIMARY KEY (Idx)
);
 CREATE NONCLUSTERED INDEX IX_AdDataMetaBreakdown_Merge ON oriodatabase.dbo.AdDataMetaBreakdown (  Date ASC  , AdID ASC  , BreakdownType ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.AdDataNaver definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.AdDataNaver;

CREATE TABLE oriodatabase.dbo.AdDataNaver (
	Idx bigint IDENTITY(1,1) NOT NULL,
	[Date] date NOT NULL,
	CampaignID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CampaignName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdGroupID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdGroupName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	KeywordID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Keyword nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	AdName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Device nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Impressions int DEFAULT 0 NULL,
	Clicks int DEFAULT 0 NULL,
	Conversions int DEFAULT 0 NULL,
	ConversionValue float DEFAULT 0 NULL,
	CollectedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK_AdDataNaver PRIMARY KEY (Idx)
);
 CREATE NONCLUSTERED INDEX IX_AdDataNaver_Date_AdID ON oriodatabase.dbo.AdDataNaver (  Date ASC  , AdID ASC  , KeywordID ASC  , Device ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.AdDataNaver_Frog definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.AdDataNaver_Frog;

CREATE TABLE oriodatabase.dbo.AdDataNaver_Frog (
	Idx bigint IDENTITY(1,1) NOT NULL,
	[Date] date NOT NULL,
	CampaignID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CampaignName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdGroupID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdGroupName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	KeywordID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Keyword nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	AdName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Device nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Impressions int DEFAULT 0 NULL,
	Clicks int DEFAULT 0 NULL,
	Conversions int DEFAULT 0 NULL,
	ConversionValue float DEFAULT 0 NULL,
	CollectedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK_AdDataNaver_Frog PRIMARY KEY (Idx)
);
 CREATE NONCLUSTERED INDEX IX_AdDataNaver_Frog_Date_AdID ON oriodatabase.dbo.AdDataNaver_Frog (  Date ASC  , AdID ASC  , KeywordID ASC  , Device ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.Brand definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Brand;

CREATE TABLE oriodatabase.dbo.Brand (
	BrandID int IDENTITY(1,1) NOT NULL,
	Name nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	UpdatedDate datetime2 DEFAULT getdate() NULL,
	Title nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsActive bit DEFAULT 1 NOT NULL,
	BrandCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK_Brand PRIMARY KEY (BrandID)
);
 CREATE NONCLUSTERED INDEX IX_Brand_IsActive ON oriodatabase.dbo.Brand (  IsActive ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.Cafe24Customers definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Cafe24Customers;

CREATE TABLE oriodatabase.dbo.Cafe24Customers (
	CustomerID int IDENTITY(1,1) NOT NULL,
	member_id nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	shop_no int NULL,
	group_no int NULL,
	member_authentication nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	authentication_method nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	sms nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	news_mail nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	gender nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	total_points decimal(18,2) NULL,
	available_points decimal(18,2) NULL,
	used_points decimal(18,2) NULL,
	use_mobile_app nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	last_login_date datetime2 NULL,
	created_date datetime2 NULL,
	fixed_group nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	next_grade nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	total_purchase_amount decimal(18,2) NULL,
	total_purchase_count int NULL,
	required_purchase_amount decimal(18,2) NULL,
	required_purchase_count int NULL,
	BlobPath nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CollectedDate datetime2 DEFAULT getdate() NULL,
	phone nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	cellphone nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__Cafe24Cu__A4AE64B8A716F9FD PRIMARY KEY (CustomerID),
	CONSTRAINT UQ__Cafe24Cu__B29B85350550E86F UNIQUE (member_id)
);
 CREATE NONCLUSTERED INDEX IX_Cafe24Customers_created_date ON oriodatabase.dbo.Cafe24Customers (  created_date ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Cafe24Customers_group_no ON oriodatabase.dbo.Cafe24Customers (  group_no ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Cafe24Customers_member_id ON oriodatabase.dbo.Cafe24Customers (  member_id ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.Cafe24Orders definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Cafe24Orders;

CREATE TABLE oriodatabase.dbo.Cafe24Orders (
	Cafe24OrderID int IDENTITY(1,1) NOT NULL,
	order_id nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	order_date datetime NULL,
	payment_date datetime NULL,
	shipped_date datetime NULL,
	purchaseconfirmation_date datetime NULL,
	order_status nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	shipping_status nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	member_id nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	billing_name nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	member_email nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	order_place_name nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	order_from_mobile bit NULL,
	order_price_amount decimal(18,2) NULL,
	shipping_fee decimal(18,2) NULL,
	coupon_discount_price decimal(18,2) NULL,
	points_spent_amount decimal(18,2) NULL,
	payment_amount decimal(18,2) NULL,
	payment_method nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	payment_gateway_names nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	paid bit NULL,
	canceled bit NULL,
	cancel_date datetime NULL,
	first_order bit NULL,
	BlobPath nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CollectedDate datetime DEFAULT getdate() NOT NULL,
	CONSTRAINT PK_Cafe24Orders PRIMARY KEY (Cafe24OrderID),
	CONSTRAINT UQ_Cafe24Orders_order_id UNIQUE (order_id)
);
 CREATE NONCLUSTERED INDEX IX_Cafe24Orders_member_id ON oriodatabase.dbo.Cafe24Orders (  member_id ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Cafe24Orders_order_date ON oriodatabase.dbo.Cafe24Orders (  order_date DESC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Cafe24Orders_payment_date ON oriodatabase.dbo.Cafe24Orders (  payment_date DESC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Cafe24Orders_shipped_date ON oriodatabase.dbo.Cafe24Orders (  shipped_date ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Cafe24Orders_shipping_status ON oriodatabase.dbo.Cafe24Orders (  shipping_status ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.Cafe24Visitors definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Cafe24Visitors;

CREATE TABLE oriodatabase.dbo.Cafe24Visitors (
	ID int IDENTITY(1,1) NOT NULL,
	[Date] date NOT NULL,
	VisitCount int NULL,
	FirstVisitCount int NULL,
	ReVisitCount int NULL,
	CollectedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__Cafe24Vi__3214EC27AA84B7BE PRIMARY KEY (ID),
	CONSTRAINT UQ_Visitors_Date UNIQUE ([Date])
);


-- oriodatabase.dbo.Cafe24VisitpathAds definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Cafe24VisitpathAds;

CREATE TABLE oriodatabase.dbo.Cafe24VisitpathAds (
	ID int IDENTITY(1,1) NOT NULL,
	[Date] date NOT NULL,
	Ad nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	VisitCount int NULL,
	OrderCount int NULL,
	OrderAmount bigint NULL,
	JoinCount int NULL,
	CollectedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__Cafe24Vi__3214EC27B0C8730D PRIMARY KEY (ID),
	CONSTRAINT UQ_VisitpathAds_Date_Ad UNIQUE ([Date],Ad)
);


-- oriodatabase.dbo.Cafe24VisitpathDomains definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Cafe24VisitpathDomains;

CREATE TABLE oriodatabase.dbo.Cafe24VisitpathDomains (
	ID int IDENTITY(1,1) NOT NULL,
	[Date] date NOT NULL,
	[Domain] nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	VisitCount int NULL,
	OrderCount int NULL,
	OrderAmount bigint NULL,
	CollectedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__Cafe24Vi__3214EC2706E7A52F PRIMARY KEY (ID),
	CONSTRAINT UQ_VisitpathDomains_Date_Domain UNIQUE ([Date],[Domain])
);


-- oriodatabase.dbo.Cafe24VisitpathKeywords definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Cafe24VisitpathKeywords;

CREATE TABLE oriodatabase.dbo.Cafe24VisitpathKeywords (
	ID int IDENTITY(1,1) NOT NULL,
	[Date] date NOT NULL,
	Keyword nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	VisitCount int NULL,
	OrderCount int NULL,
	OrderAmount bigint NULL,
	CollectedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__Cafe24Vi__3214EC272E8EDA50 PRIMARY KEY (ID),
	CONSTRAINT UQ_VisitpathKeywords_Date_Keyword UNIQUE ([Date],Keyword)
);


-- oriodatabase.dbo.ChangeLog definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.ChangeLog;

CREATE TABLE oriodatabase.dbo.ChangeLog (
	ChangeID bigint IDENTITY(1,1) NOT NULL,
	TableName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	RecordID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	FieldName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	OldValue nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	NewValue nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ChangedBy int NOT NULL,
	ChangedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__ChangeLo__0E05C5B776674BA1 PRIMARY KEY (ChangeID)
);
 CREATE NONCLUSTERED INDEX IX_ChangeLog_ChangedBy ON oriodatabase.dbo.ChangeLog (  ChangedBy ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ChangeLog_ChangedDate ON oriodatabase.dbo.ChangeLog (  ChangedDate DESC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ChangeLog_Table_Record ON oriodatabase.dbo.ChangeLog (  TableName ASC  , RecordID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.Channel definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Channel;

CREATE TABLE oriodatabase.dbo.Channel (
	ChannelID int IDENTITY(1,1) NOT NULL,
	Name nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	[Group] nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	[Type] nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ContractType nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Owner nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	LiveSource nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	UpdatedDate datetime2 DEFAULT getdate() NULL,
	SabangnetMallID nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK_Channel PRIMARY KEY (ChannelID)
);
 CREATE NONCLUSTERED INDEX IX_Channel_LiveSource ON oriodatabase.dbo.Channel (  LiveSource ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Channel_SabangnetMallID ON oriodatabase.dbo.Channel (  SabangnetMallID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.Expected1PIrregular definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Expected1PIrregular;

CREATE TABLE oriodatabase.dbo.Expected1PIrregular (
	Expected1PIrregularID nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	IrregularName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IrregularType nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	StartDate date NOT NULL,
	StartTime time DEFAULT '00:00:00' NOT NULL,
	EndDate date NOT NULL,
	EndTime time DEFAULT '23:59:59' NOT NULL,
	Status nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS DEFAULT 'SCHEDULED' NULL,
	BrandID int NOT NULL,
	BrandName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ChannelID int NOT NULL,
	ChannelName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CommissionRate decimal(5,2) NULL,
	DiscountOwner nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CompanyShare decimal(5,2) NULL,
	ChannelShare decimal(5,2) NULL,
	ExpectedSalesAmount decimal(18,2) NULL,
	ExpectedQuantity int NULL,
	Notes nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	InputMonth nvarchar(7) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	OliveyoungType nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__Expected__9FC72FAFC26B2D15 PRIMARY KEY (Expected1PIrregularID)
);


-- oriodatabase.dbo.Expected1PRegularProduct definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Expected1PRegularProduct;

CREATE TABLE oriodatabase.dbo.Expected1PRegularProduct (
	Expected1PRegularID int IDENTITY(1,1) NOT NULL,
	[Date] date NOT NULL,
	BrandID int NOT NULL,
	BrandName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ChannelID int NOT NULL,
	ChannelName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ERPCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	UniqueCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ProductName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ExpectedAmount decimal(18,2) NULL,
	ExpectedAmountExVAT decimal(18,2) NULL,
	ExpectedQuantity int NULL,
	Notes nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	OliveyoungType nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS DEFAULT '' NULL,
	InputMonth nvarchar(7) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__Expected__6E569AF373146490 PRIMARY KEY (Expected1PRegularID),
	CONSTRAINT UQ_Exp1PRegular UNIQUE ([Date],UniqueCode,ChannelID,InputMonth,OliveyoungType)
);


-- oriodatabase.dbo.Expected3PRegularProduct definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Expected3PRegularProduct;

CREATE TABLE oriodatabase.dbo.Expected3PRegularProduct (
	Expected3PRegularID int IDENTITY(1,1) NOT NULL,
	[Date] date NOT NULL,
	BrandID int NOT NULL,
	BrandName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ChannelID int NOT NULL,
	ChannelName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	UniqueCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ProductName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ExpectedAmount decimal(18,2) NULL,
	ExpectedQuantity int NULL,
	Notes nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	ExpectedAmountExVAT decimal(18,2) NULL,
	ERPCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	InputMonth nvarchar(7) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	CONSTRAINT PK__TargetBa__2E1897593118F643 PRIMARY KEY (Expected3PRegularID),
	CONSTRAINT UQ_Exp3PRegular UNIQUE ([Date],UniqueCode,ChannelID,InputMonth)
);


-- oriodatabase.dbo.FrogCafe24Customers definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.FrogCafe24Customers;

CREATE TABLE oriodatabase.dbo.FrogCafe24Customers (
	CustomerID int IDENTITY(1,1) NOT NULL,
	member_id nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	shop_no int NULL,
	group_no int NULL,
	phone nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	cellphone nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	member_authentication bit NULL,
	authentication_method nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	sms bit NULL,
	news_mail bit NULL,
	gender nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	total_points int NULL,
	available_points int NULL,
	used_points int NULL,
	use_mobile_app bit NULL,
	fixed_group bit NULL,
	last_login_date datetime NULL,
	created_date datetime NULL,
	next_grade nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	total_purchase_amount decimal(18,2) NULL,
	total_purchase_count int NULL,
	required_purchase_amount decimal(18,2) NULL,
	required_purchase_count int NULL,
	CollectedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__FrogCafe__A4AE64B841D7B59E PRIMARY KEY (CustomerID)
);
 CREATE UNIQUE NONCLUSTERED INDEX UX_FrogCafe24Customers_member_id ON oriodatabase.dbo.FrogCafe24Customers (  member_id ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.FrogCafe24Orders definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.FrogCafe24Orders;

CREATE TABLE oriodatabase.dbo.FrogCafe24Orders (
	Cafe24OrderID int IDENTITY(1,1) NOT NULL,
	order_id nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	order_date datetime NULL,
	payment_date datetime NULL,
	order_status nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	shipping_status nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	shipped_date datetime NULL,
	purchaseconfirmation_date datetime NULL,
	member_id nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	billing_name nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	member_email nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	order_place_name nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	order_from_mobile bit NULL,
	order_price_amount decimal(18,2) NULL,
	shipping_fee decimal(18,2) NULL,
	coupon_discount_price decimal(18,2) NULL,
	points_spent_amount decimal(18,2) NULL,
	payment_amount decimal(18,2) NULL,
	payment_method nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	payment_gateway_names nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	paid bit NULL,
	canceled bit NULL,
	cancel_date datetime NULL,
	first_order bit NULL,
	CollectedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__FrogCafe__B61C31D8D7654C6C PRIMARY KEY (Cafe24OrderID)
);
 CREATE UNIQUE NONCLUSTERED INDEX UX_FrogCafe24Orders_order_id ON oriodatabase.dbo.FrogCafe24Orders (  order_id ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.FrogCafe24OrdersDetail definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.FrogCafe24OrdersDetail;

CREATE TABLE oriodatabase.dbo.FrogCafe24OrdersDetail (
	DetailID int IDENTITY(1,1) NOT NULL,
	Cafe24OrderID int NULL,
	order_id nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	order_item_code nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	item_no int NULL,
	ProductUniqueCode nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ProductID int NULL,
	custom_product_code nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	custom_variant_code nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	product_name nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	option_value nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	quantity int NULL,
	product_price decimal(18,2) NULL,
	payment_amount decimal(18,2) NULL,
	coupon_discount_price decimal(18,2) NULL,
	order_status nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	order_status_additional_info nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	shipping_code nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	shipping_company_name nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	tracking_no nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	product_bundle bit NULL,
	supplier_id nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	made_in_code nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CollectedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__FrogCafe__135C314D30EB3A7C PRIMARY KEY (DetailID)
);
 CREATE UNIQUE NONCLUSTERED INDEX UX_FrogCafe24OrdersDetail_order_item_code ON oriodatabase.dbo.FrogCafe24OrdersDetail (  order_item_code ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.GoogleAdsSearchVolume definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.GoogleAdsSearchVolume;

CREATE TABLE oriodatabase.dbo.GoogleAdsSearchVolume (
	ID int IDENTITY(1,1) NOT NULL,
	KeywordID int NOT NULL,
	BrandID int NOT NULL,
	Keyword nvarchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	AvgMonthlySearches bigint NULL,
	Competition nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CompetitionIndex int NULL,
	LowTopOfPageBid float NULL,
	HighTopOfPageBid float NULL,
	MonthlyHistory nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CollectionDate date NOT NULL,
	CONSTRAINT PK__GoogleAd__3214EC27466DD405 PRIMARY KEY (ID)
);
 CREATE NONCLUSTERED INDEX IX_GoogleAds_Keyword_Date ON oriodatabase.dbo.GoogleAdsSearchVolume (  KeywordID ASC  , CollectionDate ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.IrregularType definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.IrregularType;

CREATE TABLE oriodatabase.dbo.IrregularType (
	TypeCode nvarchar(5) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	TypeName nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	DisplayName nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Category nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	CONSTRAINT PK__Promotio__3E1CDC7D5A999E83 PRIMARY KEY (TypeCode)
);


-- oriodatabase.dbo.Permission definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Permission;

CREATE TABLE oriodatabase.dbo.Permission (
	PermissionID int IDENTITY(1,1) NOT NULL,
	Module nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	[Action] nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Name nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Description nvarchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__Permissi__EFA6FB0F41B496BF PRIMARY KEY (PermissionID),
	CONSTRAINT UQ_Permission_Module_Action UNIQUE (Module,[Action])
);
 CREATE NONCLUSTERED INDEX IX_Permission_Module ON oriodatabase.dbo.Permission (  Module ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.[Role] definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.[Role];

CREATE TABLE oriodatabase.dbo.[Role] (
	RoleID int IDENTITY(1,1) NOT NULL,
	Name nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Description nvarchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__Role__8AFACE3AB5D73B22 PRIMARY KEY (RoleID),
	CONSTRAINT UQ__Role__737584F6EA11CA36 UNIQUE (Name)
);


-- oriodatabase.dbo.SabangnetReceivingPlan definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.SabangnetReceivingPlan;

CREATE TABLE oriodatabase.dbo.SabangnetReceivingPlan (
	ReceivingPlanID int NOT NULL,
	MemberID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ReceivingPlanCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PlanDate nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PlanStatus int NULL,
	CompleteDt nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Memo nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	LastSyncedAt datetime DEFAULT getdate() NULL,
	CreatedAt datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__Sabangne__6CC186CB90BFE840 PRIMARY KEY (ReceivingPlanID)
);
 CREATE NONCLUSTERED INDEX IX_RecvPlan_PlanDate ON oriodatabase.dbo.SabangnetReceivingPlan (  PlanDate ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_RecvPlan_PlanStatus ON oriodatabase.dbo.SabangnetReceivingPlan (  PlanStatus ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.SystemConfig definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.SystemConfig;

CREATE TABLE oriodatabase.dbo.SystemConfig (
	ConfigID int IDENTITY(1,1) NOT NULL,
	Category nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ConfigKey nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ConfigValue nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	DataType nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS DEFAULT 'string' NULL,
	Description nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsActive bit DEFAULT 1 NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	UpdatedBy nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__SystemCo__C3BC333CFF65F167 PRIMARY KEY (ConfigID),
	CONSTRAINT UQ_SystemConfig_Category_Key UNIQUE (Category,ConfigKey)
);
 CREATE NONCLUSTERED INDEX IX_SystemConfig_Category ON oriodatabase.dbo.SystemConfig (  Category ASC  , IsActive ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_SystemConfig_Key ON oriodatabase.dbo.SystemConfig (  ConfigKey ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.SystemConfigHistory definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.SystemConfigHistory;

CREATE TABLE oriodatabase.dbo.SystemConfigHistory (
	HistoryID int IDENTITY(1,1) NOT NULL,
	ConfigID int NOT NULL,
	Category nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ConfigKey nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	OldValue nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	NewValue nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ChangedBy nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ChangedDate datetime DEFAULT getdate() NULL,
	ChangeReason nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__SystemCo__4D7B4ADDF11F32D0 PRIMARY KEY (HistoryID)
);
 CREATE NONCLUSTERED INDEX IX_SystemConfigHistory_ChangedDate ON oriodatabase.dbo.SystemConfigHistory (  ChangedDate DESC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_SystemConfigHistory_ConfigID ON oriodatabase.dbo.SystemConfigHistory (  ConfigID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.[User] definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.[User];

CREATE TABLE oriodatabase.dbo.[User] (
	UserID int IDENTITY(1,1) NOT NULL,
	Email nvarchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	PasswordHash nvarchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Name nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	IsActive bit DEFAULT 1 NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	LastLoginDate datetime NULL,
	CreatedBy int NULL,
	CONSTRAINT PK__User__1788CCACEE516C13 PRIMARY KEY (UserID),
	CONSTRAINT UQ__User__A9D10534139AAD13 UNIQUE (Email)
);
 CREATE NONCLUSTERED INDEX IX_User_Email ON oriodatabase.dbo.User (  Email ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.Vendor definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Vendor;

CREATE TABLE oriodatabase.dbo.Vendor (
	VendorID int IDENTITY(1,1) NOT NULL,
	Name nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Country nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Currency nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ShippingMethod nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK_Vendor PRIMARY KEY (VendorID)
);


-- oriodatabase.dbo.ViralKeywords definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.ViralKeywords;

CREATE TABLE oriodatabase.dbo.ViralKeywords (
	KeywordID int IDENTITY(1,1) NOT NULL,
	BrandName nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	KeywordType nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Keyword nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	IsActive bit DEFAULT 1 NULL,
	Description nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	UpdatedBy nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS DEFAULT 'SYSTEM' NULL,
	CONSTRAINT PK__ViralKey__37C135C123F1C986 PRIMARY KEY (KeywordID)
);
 CREATE NONCLUSTERED INDEX IX_ViralKeywords_Brand_Type ON oriodatabase.dbo.ViralKeywords (  BrandName ASC  , KeywordType ASC  , IsActive ASC  )  
	 INCLUDE ( Keyword ) 
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.Warehouse definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Warehouse;

CREATE TABLE oriodatabase.dbo.Warehouse (
	WarehouseID int IDENTITY(1,1) NOT NULL,
	WarehouseName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	CONSTRAINT PK_Warehouse PRIMARY KEY (WarehouseID),
	CONSTRAINT UQ_Warehouse_Name UNIQUE (WarehouseName)
);


-- oriodatabase.dbo.WithdrawalPlan definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.WithdrawalPlan;

CREATE TABLE oriodatabase.dbo.WithdrawalPlan (
	PlanID int IDENTITY(1,1) NOT NULL,
	GroupID int NOT NULL,
	Title nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	[Date] date NOT NULL,
	[Type] nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ProductName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	UniqueCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PlannedQty int DEFAULT 1 NOT NULL,
	Notes nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreatedBy int NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	ERPCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	InputMonth nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__Withdraw__755C22D76E54EE77 PRIMARY KEY (PlanID)
);
 CREATE NONCLUSTERED INDEX IX_WithdrawalPlan_Date ON oriodatabase.dbo.WithdrawalPlan (  Date ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_WithdrawalPlan_GroupID ON oriodatabase.dbo.WithdrawalPlan (  GroupID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_WithdrawalPlan_Title ON oriodatabase.dbo.WithdrawalPlan (  Title ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_WithdrawalPlan_Type ON oriodatabase.dbo.WithdrawalPlan (  Type ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_WithdrawalPlan_UniqueCode ON oriodatabase.dbo.WithdrawalPlan (  UniqueCode ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.ActivityLog definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.ActivityLog;

CREATE TABLE oriodatabase.dbo.ActivityLog (
	LogID bigint IDENTITY(1,1) NOT NULL,
	UserID int NOT NULL,
	ActionType nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	TargetTable nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	TargetID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Details nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IPAddress nvarchar(45) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__Activity__5E5499A817D7B9C3 PRIMARY KEY (LogID),
	CONSTRAINT FK__ActivityL__UserI__13A7DD28 FOREIGN KEY (UserID) REFERENCES oriodatabase.dbo.[User](UserID)
);
 CREATE NONCLUSTERED INDEX IX_ActivityLog_ActionType ON oriodatabase.dbo.ActivityLog (  ActionType ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ActivityLog_CreatedDate ON oriodatabase.dbo.ActivityLog (  CreatedDate DESC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ActivityLog_UserID ON oriodatabase.dbo.ActivityLog (  UserID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.AdContractNaver definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.AdContractNaver;

CREATE TABLE oriodatabase.dbo.AdContractNaver (
	ContractID int IDENTITY(1,1) NOT NULL,
	ContractName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	BrandID int NULL,
	AdGroupID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	StartDate date NOT NULL,
	EndDate date NOT NULL,
	TotalBudget decimal(18,2) NOT NULL,
	IsActive bit DEFAULT 1 NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	AdGroupName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__AdContra__C90D3409C5FB26BF PRIMARY KEY (ContractID),
	CONSTRAINT FK_AdContractNaver_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID)
);
 CREATE NONCLUSTERED INDEX IX_AdContractNaver_BrandID ON oriodatabase.dbo.AdContractNaver (  BrandID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_AdContractNaver_Dates ON oriodatabase.dbo.AdContractNaver (  StartDate ASC  , EndDate ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.Cafe24OrdersDetail definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Cafe24OrdersDetail;

CREATE TABLE oriodatabase.dbo.Cafe24OrdersDetail (
	DetailID int IDENTITY(1,1) NOT NULL,
	Cafe24OrderID int NULL,
	order_id nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	order_item_code nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	item_no int NULL,
	ProductUniqueCode nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ProductID int NULL,
	custom_product_code nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	custom_variant_code nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	product_name nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	option_value nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	quantity int NULL,
	product_price decimal(18,2) NULL,
	payment_amount decimal(18,2) NULL,
	coupon_discount_price decimal(18,2) NULL,
	order_status nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	order_status_additional_info nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	shipping_code nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	shipping_company_name nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	tracking_no nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	product_bundle bit NULL,
	supplier_id nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	made_in_code nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CollectedDate datetime DEFAULT getdate() NOT NULL,
	CONSTRAINT PK_Cafe24OrdersDetail PRIMARY KEY (DetailID),
	CONSTRAINT UQ_Cafe24OrdersDetail_order_item_code UNIQUE (order_item_code),
	CONSTRAINT FK_Cafe24OrdersDetail_Cafe24Orders FOREIGN KEY (Cafe24OrderID) REFERENCES oriodatabase.dbo.Cafe24Orders(Cafe24OrderID) ON DELETE SET NULL
);
 CREATE NONCLUSTERED INDEX IX_Cafe24OrdersDetail_Cafe24OrderID ON oriodatabase.dbo.Cafe24OrdersDetail (  Cafe24OrderID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Cafe24OrdersDetail_ProductID ON oriodatabase.dbo.Cafe24OrdersDetail (  ProductID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Cafe24OrdersDetail_ProductUniqueCode ON oriodatabase.dbo.Cafe24OrdersDetail (  ProductUniqueCode ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Cafe24OrdersDetail_custom_product_code ON oriodatabase.dbo.Cafe24OrdersDetail (  custom_product_code ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Cafe24OrdersDetail_custom_variant_code ON oriodatabase.dbo.Cafe24OrdersDetail (  custom_variant_code ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Cafe24OrdersDetail_order_id ON oriodatabase.dbo.Cafe24OrdersDetail (  order_id ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.ChannelDetail definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.ChannelDetail;

CREATE TABLE oriodatabase.dbo.ChannelDetail (
	ChannelDetailID int IDENTITY(1,1) NOT NULL,
	ChannelID int NULL,
	BizNumber nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	DetailName nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	UpdatedDate datetime2 DEFAULT getdate() NULL,
	CONSTRAINT PK_ChannelDetail PRIMARY KEY (ChannelDetailID),
	CONSTRAINT FK_ChannelDetail_Channel FOREIGN KEY (ChannelID) REFERENCES oriodatabase.dbo.Channel(ChannelID)
);
 CREATE NONCLUSTERED INDEX IX_ChannelDetail_ChannelID ON oriodatabase.dbo.ChannelDetail (  ChannelID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.Expected1PIrregularProduct definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Expected1PIrregularProduct;

CREATE TABLE oriodatabase.dbo.Expected1PIrregularProduct (
	Expected1PIrregularProductID int IDENTITY(1,1) NOT NULL,
	Expected1PIrregularID nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ERPCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	UniqueCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ProductName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SellingPrice decimal(18,2) NULL,
	IrregularPrice decimal(18,2) NULL,
	SupplyPrice decimal(18,2) NULL,
	CouponDiscountRate decimal(5,2) NULL,
	UnitCost decimal(18,2) NULL,
	LogisticsCost decimal(18,2) NULL,
	ManagementCost decimal(18,2) NULL,
	WarehouseCost decimal(18,2) NULL,
	EDICost decimal(18,2) NULL,
	MisCost decimal(18,2) NULL,
	ExpectedSalesAmount decimal(18,2) NULL,
	ExpectedQuantity int NULL,
	Notes nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	ExpectedSalesAmountExVAT float NULL,
	CONSTRAINT PK__Expected__470FEA24D92077A1 PRIMARY KEY (Expected1PIrregularProductID),
	CONSTRAINT FK_Exp1PIrregProd_Irreg FOREIGN KEY (Expected1PIrregularID) REFERENCES oriodatabase.dbo.Expected1PIrregular(Expected1PIrregularID)
);


-- oriodatabase.dbo.Expected3PIrregular definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Expected3PIrregular;

CREATE TABLE oriodatabase.dbo.Expected3PIrregular (
	Expected3PIrregularID nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	IrregularName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	IrregularType nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	StartDate date NOT NULL,
	StartTime time DEFAULT '00:00:00' NOT NULL,
	EndDate date NOT NULL,
	EndTime time DEFAULT '23:59:59' NOT NULL,
	Status nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS DEFAULT 'SCHEDULED' NULL,
	BrandID int NOT NULL,
	BrandName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ChannelID int NOT NULL,
	ChannelName nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CommissionRate decimal(5,2) NULL,
	DiscountOwner nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CompanyShare decimal(5,2) NULL,
	ChannelShare decimal(5,2) NULL,
	ExpectedSalesAmount decimal(18,2) NULL,
	ExpectedQuantity int NULL,
	Notes nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	InputMonth nvarchar(7) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__Promotio__52C42F2FB81831C0 PRIMARY KEY (Expected3PIrregularID),
	CONSTRAINT FK_Promotion_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID)
);


-- oriodatabase.dbo.Expected3PIrregularProduct definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Expected3PIrregularProduct;

CREATE TABLE oriodatabase.dbo.Expected3PIrregularProduct (
	Expected3PIrregularProductID int IDENTITY(1,1) NOT NULL,
	Expected3PIrregularID nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	UniqueCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ProductName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SellingPrice decimal(18,2) NULL,
	IrregularPrice decimal(18,2) NULL,
	SupplyPrice decimal(18,2) NULL,
	CouponDiscountRate decimal(5,2) NULL,
	UnitCost decimal(18,2) NULL,
	LogisticsCost decimal(18,2) NULL,
	ManagementCost decimal(18,2) NULL,
	WarehouseCost decimal(18,2) NULL,
	EDICost decimal(18,2) NULL,
	MisCost decimal(18,2) NULL,
	ExpectedSalesAmount decimal(18,2) NULL,
	ExpectedQuantity int NULL,
	Notes nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	ERPCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ExpectedSalesAmountExVAT float NULL,
	CONSTRAINT PK__Promotio__C7B85D3CBB631920 PRIMARY KEY (Expected3PIrregularProductID),
	CONSTRAINT UQ_PromotionProduct UNIQUE (Expected3PIrregularID,UniqueCode),
	CONSTRAINT FK_IrregularProduct_Irregular FOREIGN KEY (Expected3PIrregularID) REFERENCES oriodatabase.dbo.Expected3PIrregular(Expected3PIrregularID)
);


-- oriodatabase.dbo.Keyword definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Keyword;

CREATE TABLE oriodatabase.dbo.Keyword (
	KeywordID int IDENTITY(1,1) NOT NULL,
	Keyword nvarchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	BrandID int NOT NULL,
	Category nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Priority int DEFAULT 5 NULL,
	IsActive bit DEFAULT 1 NOT NULL,
	CollectNaverAds bit DEFAULT 1 NULL,
	CollectGoogleAds bit DEFAULT 1 NULL,
	CreatedDate datetime DEFAULT getdate() NOT NULL,
	UpdatedDate datetime DEFAULT getdate() NOT NULL,
	CONSTRAINT PK__Keyword__37C135C166837891 PRIMARY KEY (KeywordID),
	CONSTRAINT UQ_Keyword_Keyword_Brand UNIQUE (Keyword,BrandID),
	CONSTRAINT FK_Keyword_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID)
);
 CREATE NONCLUSTERED INDEX IX_Keyword_BrandID ON oriodatabase.dbo.Keyword (  BrandID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Keyword_Category ON oriodatabase.dbo.Keyword (  Category ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Keyword_IsActive ON oriodatabase.dbo.Keyword (  IsActive ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_Keyword_Priority ON oriodatabase.dbo.Keyword (  Priority ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.NaverAdsSearchVolume definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.NaverAdsSearchVolume;

CREATE TABLE oriodatabase.dbo.NaverAdsSearchVolume (
	ID int IDENTITY(1,1) NOT NULL,
	KeywordID int NOT NULL,
	BrandID int NOT NULL,
	MonthlyPcSearchCount int NOT NULL,
	MonthlyMobileSearchCount int NOT NULL,
	MonthlyTotalSearchCount int NOT NULL,
	MonthlyAvgPcClickCount decimal(10,2) NULL,
	MonthlyAvgMobileClickCount decimal(10,2) NULL,
	MonthlyAvgPcCtr decimal(10,2) NULL,
	MonthlyAvgMobileCtr decimal(10,2) NULL,
	CompetitionIndex nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AvgAdDepth decimal(10,2) NULL,
	CollectionDate date NOT NULL,
	CreatedDate datetime DEFAULT getdate() NOT NULL,
	IsMainKeyword bit DEFAULT 0 NOT NULL,
	Keyword nvarchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	CompoundKeyword nvarchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	CONSTRAINT PK__NaverAds__3214EC27124BE1AA PRIMARY KEY (ID),
	CONSTRAINT UQ_NaverAdsSearchVolume_KeywordID_CompoundKeyword_Date UNIQUE (KeywordID,CompoundKeyword,CollectionDate),
	CONSTRAINT FK_NaverAdsSearchVolume_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID),
	CONSTRAINT FK_NaverAdsSearchVolume_Keyword FOREIGN KEY (KeywordID) REFERENCES oriodatabase.dbo.Keyword(KeywordID)
);
 CREATE NONCLUSTERED INDEX IX_NaverAdsSearchVolume_BrandID ON oriodatabase.dbo.NaverAdsSearchVolume (  BrandID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_NaverAdsSearchVolume_Brand_Date ON oriodatabase.dbo.NaverAdsSearchVolume (  BrandID ASC  , CollectionDate ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_NaverAdsSearchVolume_CollectionDate ON oriodatabase.dbo.NaverAdsSearchVolume (  CollectionDate ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_NaverAdsSearchVolume_IsMainKeyword ON oriodatabase.dbo.NaverAdsSearchVolume (  IsMainKeyword ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_NaverAdsSearchVolume_TotalSearch ON oriodatabase.dbo.NaverAdsSearchVolume (  MonthlyTotalSearchCount DESC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.Product definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Product;

CREATE TABLE oriodatabase.dbo.Product (
	ProductID int IDENTITY(1,1) NOT NULL,
	BrandID int NULL,
	UniqueCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Name nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	TypeERP nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	TypeDB nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	BaseBarcode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Barcode2 nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SabangnetCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SabangnetUniqueCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	BundleType nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CategoryMid nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CategorySub nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Status nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ReleaseDate datetime2 DEFAULT getdate() NULL,
	UpdatedDate datetime2 DEFAULT getdate() NULL,
	ProductType nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS DEFAULT 'SINGLE' NULL,
	CONSTRAINT PK_Product PRIMARY KEY (ProductID),
	CONSTRAINT FK_Product_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID)
);
 CREATE NONCLUSTERED INDEX IX_Product_BrandID ON oriodatabase.dbo.Product (  BrandID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE UNIQUE NONCLUSTERED INDEX UQ_Product_UniqueCode ON oriodatabase.dbo.Product (  UniqueCode ASC  )  
	 WHERE  ([UniqueCode] IS NOT NULL)
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.ProductBox definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.ProductBox;

CREATE TABLE oriodatabase.dbo.ProductBox (
	BoxID int IDENTITY(1,1) NOT NULL,
	ProductID int NULL,
	ERPCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	QuantityInBox int NULL,
	UpdatedDate datetime2 DEFAULT getdate() NULL,
	CoupangSKU nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	UnitCostKRW decimal(18,2) NULL,
	SalesPrice decimal(18,2) NULL,
	SupplyPrice decimal(18,2) NULL,
	CONSTRAINT PK_ProductBox PRIMARY KEY (BoxID),
	CONSTRAINT FK_ProductBox_Product FOREIGN KEY (ProductID) REFERENCES oriodatabase.dbo.Product(ProductID)
);
 CREATE NONCLUSTERED INDEX IX_ProductBox_ProductID ON oriodatabase.dbo.ProductBox (  ProductID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE UNIQUE NONCLUSTERED INDEX UQ_ProductBox_ERPCode ON oriodatabase.dbo.ProductBox (  ERPCode ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.ProductDisbursement definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.ProductDisbursement;

CREATE TABLE oriodatabase.dbo.ProductDisbursement (
	DisbursementID int IDENTITY(1,1) NOT NULL,
	Title nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	[Type] nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Status nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS DEFAULT 'DRAFT' NOT NULL,
	RequestedBy int NOT NULL,
	RequestDate datetime DEFAULT getdate() NULL,
	ApprovedBy int NULL,
	ApprovalDate datetime NULL,
	RejectionReason nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	RecipientName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	RecipientContact nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Notes nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	UpdatedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__ProductD__3EF9329BCAC1CF88 PRIMARY KEY (DisbursementID),
	CONSTRAINT FK_ProductDisbursement_ApprovedBy FOREIGN KEY (ApprovedBy) REFERENCES oriodatabase.dbo.[User](UserID),
	CONSTRAINT FK_ProductDisbursement_RequestedBy FOREIGN KEY (RequestedBy) REFERENCES oriodatabase.dbo.[User](UserID)
);
 CREATE NONCLUSTERED INDEX IX_ProductDisbursement_RequestDate ON oriodatabase.dbo.ProductDisbursement (  RequestDate DESC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ProductDisbursement_RequestedBy ON oriodatabase.dbo.ProductDisbursement (  RequestedBy ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ProductDisbursement_Status ON oriodatabase.dbo.ProductDisbursement (  Status ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ProductDisbursement_Type ON oriodatabase.dbo.ProductDisbursement (  Type ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
ALTER TABLE oriodatabase.dbo.ProductDisbursement WITH NOCHECK ADD CONSTRAINT CK_ProductDisbursement_Type CHECK (([Type]='OTHER' OR [Type]='INTERNAL' OR [Type]='SAMPLE' OR [Type]='SEEDING' OR [Type]='GIFT'));
ALTER TABLE oriodatabase.dbo.ProductDisbursement WITH NOCHECK ADD CONSTRAINT CK_ProductDisbursement_Status CHECK (([Status]='COMPLETED' OR [Status]='REJECTED' OR [Status]='APPROVED' OR [Status]='PENDING' OR [Status]='DRAFT'));


-- oriodatabase.dbo.RevenuePlan definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.RevenuePlan;

CREATE TABLE oriodatabase.dbo.RevenuePlan (
	PlanID int IDENTITY(1,1) NOT NULL,
	[Date] date NOT NULL,
	BrandID int NOT NULL,
	ChannelID int NOT NULL,
	PlanType nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Amount decimal(18,2) DEFAULT 0 NOT NULL,
	CreatedAt datetime2 DEFAULT getdate() NULL,
	UpdatedAt datetime2 DEFAULT getdate() NULL,
	ChannelDetail nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__RevenueP__755C22D7EF9DB387 PRIMARY KEY (PlanID),
	CONSTRAINT FK_RevenuePlan_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID),
	CONSTRAINT FK_RevenuePlan_Channel FOREIGN KEY (ChannelID) REFERENCES oriodatabase.dbo.Channel(ChannelID)
);
 CREATE NONCLUSTERED INDEX IX_RevenuePlan_PlanType ON oriodatabase.dbo.RevenuePlan (  PlanType ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
ALTER TABLE oriodatabase.dbo.RevenuePlan WITH NOCHECK ADD CONSTRAINT CK_RevenuePlan_PlanType CHECK (([PlanType]='EXPECTED' OR [PlanType]='TARGET'));


-- oriodatabase.dbo.RolePermission definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.RolePermission;

CREATE TABLE oriodatabase.dbo.RolePermission (
	RolePermissionID int IDENTITY(1,1) NOT NULL,
	RoleID int NOT NULL,
	PermissionID int NOT NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	CreatedBy int NULL,
	CONSTRAINT PK__RolePerm__120F469A686F13B5 PRIMARY KEY (RolePermissionID),
	CONSTRAINT UQ_RolePermission UNIQUE (RoleID,PermissionID),
	CONSTRAINT FK_RolePermission_Permission FOREIGN KEY (PermissionID) REFERENCES oriodatabase.dbo.Permission(PermissionID) ON DELETE CASCADE,
	CONSTRAINT FK_RolePermission_Role FOREIGN KEY (RoleID) REFERENCES oriodatabase.dbo.[Role](RoleID) ON DELETE CASCADE
);
 CREATE NONCLUSTERED INDEX IX_RolePermission_RoleID ON oriodatabase.dbo.RolePermission (  RoleID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.SabangnetInventorySnapshot definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.SabangnetInventorySnapshot;

CREATE TABLE oriodatabase.dbo.SabangnetInventorySnapshot (
	SnapshotID bigint IDENTITY(1,1) NOT NULL,
	SnapshotDate date NOT NULL,
	SnapshotTime nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ShippingProductID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ProductID int NULL,
	ProductCode nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ProductName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	TotalStock int DEFAULT 0 NULL,
	ReceivingStock int DEFAULT 0 NULL,
	NormalStock int DEFAULT 0 NULL,
	OrderStock int DEFAULT 0 NULL,
	ShippingStock int DEFAULT 0 NULL,
	DamagedStock int DEFAULT 0 NULL,
	ReturnStock int DEFAULT 0 NULL,
	KeepingStock int DEFAULT 0 NULL,
	CreatedAt datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__Sabangne__664F570BD047ECB4 PRIMARY KEY (SnapshotID),
	CONSTRAINT UQ_InvSnapshot_Date_Time_Product UNIQUE (SnapshotDate,SnapshotTime,ShippingProductID),
	CONSTRAINT FK_InvSnapshot_Product FOREIGN KEY (ProductID) REFERENCES oriodatabase.dbo.Product(ProductID)
);
 CREATE NONCLUSTERED INDEX IX_InvSnapshot_Date ON oriodatabase.dbo.SabangnetInventorySnapshot (  SnapshotDate ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_InvSnapshot_ProductID ON oriodatabase.dbo.SabangnetInventorySnapshot (  ProductID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_InvSnapshot_ShippingProductID ON oriodatabase.dbo.SabangnetInventorySnapshot (  ShippingProductID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.SabangnetLocationSnapshot definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.SabangnetLocationSnapshot;

CREATE TABLE oriodatabase.dbo.SabangnetLocationSnapshot (
	LocationSnapshotID bigint IDENTITY(1,1) NOT NULL,
	SnapshotDate date NOT NULL,
	SnapshotTime nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ShippingProductID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ProductID int NULL,
	LocationID int NULL,
	LocationName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	LocType int NULL,
	ExpireDate nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Quantity int DEFAULT 0 NULL,
	CreatedAt datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__Sabangne__540A5E0066CA2523 PRIMARY KEY (LocationSnapshotID),
	CONSTRAINT FK_LocSnapshot_Product FOREIGN KEY (ProductID) REFERENCES oriodatabase.dbo.Product(ProductID)
);
 CREATE NONCLUSTERED INDEX IX_LocSnapshot_Date ON oriodatabase.dbo.SabangnetLocationSnapshot (  SnapshotDate ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_LocSnapshot_ShippingProductID ON oriodatabase.dbo.SabangnetLocationSnapshot (  ShippingProductID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.SabangnetOrders definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.SabangnetOrders;

CREATE TABLE oriodatabase.dbo.SabangnetOrders (
	ID int IDENTITY(1,1) NOT NULL,
	IDX int NOT NULL,
	ORDER_ID nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ORDER_DATE datetime2 NOT NULL,
	ORDER_STATUS nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	MALL_ID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ChannelID int NULL,
	USER_NAME nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	USER_TEL nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	RECEIVE_TEL nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SALE_CNT int NOT NULL,
	PAY_COST decimal(10,2) NULL,
	DELV_COST decimal(10,2) NULL,
	DELIVERY_METHOD_STR nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	BRAND_NM nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ProductID int NULL,
	SET_GUBUN nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	BlobPath nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CollectedDate datetime2 DEFAULT getdate() NULL,
	DELIVERY_CONFIRM_DATE datetime2 NULL,
	CONSTRAINT PK__Sabangne__3214EC27B9DCE132 PRIMARY KEY (ID),
	CONSTRAINT FK_SabangnetOrders_Channel FOREIGN KEY (ChannelID) REFERENCES oriodatabase.dbo.Channel(ChannelID),
	CONSTRAINT FK_SabangnetOrders_Product FOREIGN KEY (ProductID) REFERENCES oriodatabase.dbo.Product(ProductID)
);
 CREATE NONCLUSTERED INDEX IX_SabangnetOrders_ChannelID ON oriodatabase.dbo.SabangnetOrders (  ChannelID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_SabangnetOrders_DeliveryConfirmDate ON oriodatabase.dbo.SabangnetOrders (  DELIVERY_CONFIRM_DATE ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_SabangnetOrders_OrderDate ON oriodatabase.dbo.SabangnetOrders (  ORDER_DATE ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_SabangnetOrders_OrderID ON oriodatabase.dbo.SabangnetOrders (  ORDER_ID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_SabangnetOrders_ProductID ON oriodatabase.dbo.SabangnetOrders (  ProductID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.SabangnetOrdersDetail definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.SabangnetOrdersDetail;

CREATE TABLE oriodatabase.dbo.SabangnetOrdersDetail (
	ID int IDENTITY(1,1) NOT NULL,
	IDX int NOT NULL,
	ORDER_ID nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	MALL_PRODUCT_ID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PRODUCT_NAME nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PRODUCT_ID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ProductID int NULL,
	P_PRODUCT_NAME nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SKU_ID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SALE_CNT int NOT NULL,
	ord_field2 nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__Sabangne__3214EC2759193238 PRIMARY KEY (ID),
	CONSTRAINT FK_SabangnetOrdersDetail_Product FOREIGN KEY (ProductID) REFERENCES oriodatabase.dbo.Product(ProductID)
);
 CREATE NONCLUSTERED INDEX IX_SabangnetOrdersDetail_OrderID ON oriodatabase.dbo.SabangnetOrdersDetail (  ORDER_ID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_SabangnetOrdersDetail_ProductID ON oriodatabase.dbo.SabangnetOrdersDetail (  ProductID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_SabangnetOrdersDetail_ord_field2 ON oriodatabase.dbo.SabangnetOrdersDetail (  ord_field2 ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.SabangnetReceivingPlanProduct definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.SabangnetReceivingPlanProduct;

CREATE TABLE oriodatabase.dbo.SabangnetReceivingPlanProduct (
	ID bigint IDENTITY(1,1) NOT NULL,
	ReceivingPlanID int NOT NULL,
	ShippingProductID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ProductID int NULL,
	Quantity int DEFAULT 0 NULL,
	ReceivingQuantity int NULL,
	PlanProductStatus int NULL,
	ExpireDate nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	MakeDate nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__Sabangne__3214EC276B81E186 PRIMARY KEY (ID),
	CONSTRAINT FK_RecvPlanProduct_Plan FOREIGN KEY (ReceivingPlanID) REFERENCES oriodatabase.dbo.SabangnetReceivingPlan(ReceivingPlanID),
	CONSTRAINT FK_RecvPlanProduct_Product FOREIGN KEY (ProductID) REFERENCES oriodatabase.dbo.Product(ProductID)
);
 CREATE NONCLUSTERED INDEX IX_RecvPlanProduct_PlanID ON oriodatabase.dbo.SabangnetReceivingPlanProduct (  ReceivingPlanID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_RecvPlanProduct_ShippingProductID ON oriodatabase.dbo.SabangnetReceivingPlanProduct (  ShippingProductID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.SabangnetReceivingWork definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.SabangnetReceivingWork;

CREATE TABLE oriodatabase.dbo.SabangnetReceivingWork (
	WorkHistoryID bigint NOT NULL,
	WorkDate nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	WorkType int NULL,
	ReceivingType int NULL,
	ReceivingPlanID int NULL,
	ShippingProductID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ProductID int NULL,
	Quantity int DEFAULT 0 NULL,
	ExpireDate nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	MakeDate nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	LocationID int NULL,
	BoxQuantity int NULL,
	PalletQuantity int NULL,
	LastSyncedAt datetime DEFAULT getdate() NULL,
	CreatedAt datetime DEFAULT getdate() NULL,
	CONSTRAINT PK__Sabangne__9C9E690D66F4858D PRIMARY KEY (WorkHistoryID),
	CONSTRAINT FK_RecvWork_Product FOREIGN KEY (ProductID) REFERENCES oriodatabase.dbo.Product(ProductID)
);
 CREATE NONCLUSTERED INDEX IX_RecvWork_ReceivingPlanID ON oriodatabase.dbo.SabangnetReceivingWork (  ReceivingPlanID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_RecvWork_ShippingProductID ON oriodatabase.dbo.SabangnetReceivingWork (  ShippingProductID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_RecvWork_WorkDate ON oriodatabase.dbo.SabangnetReceivingWork (  WorkDate ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_RecvWork_WorkType ON oriodatabase.dbo.SabangnetReceivingWork (  WorkType ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.UserPermission definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.UserPermission;

CREATE TABLE oriodatabase.dbo.UserPermission (
	UserPermissionID int IDENTITY(1,1) NOT NULL,
	UserID int NOT NULL,
	PermissionID int NOT NULL,
	[Type] nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS DEFAULT 'GRANT' NOT NULL,
	CreatedDate datetime DEFAULT getdate() NULL,
	CreatedBy int NULL,
	CONSTRAINT PK__UserPerm__A90F88D2039DC43F PRIMARY KEY (UserPermissionID),
	CONSTRAINT UQ_UserPermission UNIQUE (UserID,PermissionID),
	CONSTRAINT FK_UserPermission_Permission FOREIGN KEY (PermissionID) REFERENCES oriodatabase.dbo.Permission(PermissionID) ON DELETE CASCADE,
	CONSTRAINT FK_UserPermission_User FOREIGN KEY (UserID) REFERENCES oriodatabase.dbo.[User](UserID) ON DELETE CASCADE
);
 CREATE NONCLUSTERED INDEX IX_UserPermission_UserID ON oriodatabase.dbo.UserPermission (  UserID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
ALTER TABLE oriodatabase.dbo.UserPermission WITH NOCHECK ADD CONSTRAINT CK_UserPermission_Type CHECK (([Type]='DENY' OR [Type]='GRANT'));


-- oriodatabase.dbo.UserRole definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.UserRole;

CREATE TABLE oriodatabase.dbo.UserRole (
	UserRoleID int IDENTITY(1,1) NOT NULL,
	UserID int NOT NULL,
	RoleID int NOT NULL,
	AssignedDate datetime DEFAULT getdate() NULL,
	AssignedBy int NULL,
	CONSTRAINT PK__UserRole__3D978A559B169237 PRIMARY KEY (UserRoleID),
	CONSTRAINT UQ__UserRole__AF27604E7507C7FF UNIQUE (UserID,RoleID),
	CONSTRAINT FK__UserRole__Assign__0FD74C44 FOREIGN KEY (AssignedBy) REFERENCES oriodatabase.dbo.[User](UserID),
	CONSTRAINT FK__UserRole__RoleID__0EE3280B FOREIGN KEY (RoleID) REFERENCES oriodatabase.dbo.[Role](RoleID),
	CONSTRAINT FK__UserRole__UserID__0DEF03D2 FOREIGN KEY (UserID) REFERENCES oriodatabase.dbo.[User](UserID) ON DELETE CASCADE
);


-- oriodatabase.dbo.CoupangInventory definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.CoupangInventory;

CREATE TABLE oriodatabase.dbo.CoupangInventory (
	Idx bigint IDENTITY(1,1) NOT NULL,
	[Date] date NOT NULL,
	ProductCategory nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SubCategory nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	DetailCategory nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Brand nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Center nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SKUID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	SKUName nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Barcode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	OrderableStatus nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	OrderableStatusDetail nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	InboundQty int DEFAULT 0 NULL,
	OutboundQty int DEFAULT 0 NULL,
	CurrentStockQty int DEFAULT 0 NULL,
	PurchaseCost float DEFAULT 0 NULL,
	OrderFulfillmentRate float DEFAULT 0 NULL,
	ConfirmFulfillmentRate float DEFAULT 0 NULL,
	ReturnRate float DEFAULT 0 NULL,
	ReturnReason nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SoldOut nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	DetailCategorySoldOutRate float DEFAULT 0 NULL,
	BoxID int NULL,
	BrandID int NULL,
	CollectedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK_CoupangInventory PRIMARY KEY (Idx),
	CONSTRAINT FK_CoupangInventory_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID),
	CONSTRAINT FK_CoupangInventory_ProductBox FOREIGN KEY (BoxID) REFERENCES oriodatabase.dbo.ProductBox(BoxID)
);
 CREATE NONCLUSTERED INDEX IX_CoupangInventory_BoxID ON oriodatabase.dbo.CoupangInventory (  BoxID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_CoupangInventory_BrandID ON oriodatabase.dbo.CoupangInventory (  BrandID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_CoupangInventory_Date_SKUID ON oriodatabase.dbo.CoupangInventory (  Date ASC  , SKUID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.CoupangSales definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.CoupangSales;

CREATE TABLE oriodatabase.dbo.CoupangSales (
	Idx bigint IDENTITY(1,1) NOT NULL,
	[Date] date NOT NULL,
	ProductID_Coupang nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Barcode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SKUID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	SKUName nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	VendorItemID nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	VendorItemName nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsRocketFresh nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ProductCategory nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SubCategory nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	DetailCategory nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Brand nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	GMV float DEFAULT 0 NULL,
	UnitsSold int DEFAULT 0 NULL,
	ReturnUnits int DEFAULT 0 NULL,
	COGS float DEFAULT 0 NULL,
	AMV float DEFAULT 0 NULL,
	CouponDiscount float DEFAULT 0 NULL,
	CoupangExtraDiscount float DEFAULT 0 NULL,
	InstantDiscount float DEFAULT 0 NULL,
	PromoGMV float DEFAULT 0 NULL,
	PromoUnitsSold int DEFAULT 0 NULL,
	ASP float DEFAULT 0 NULL,
	OrderCount int DEFAULT 0 NULL,
	OrderCustomerCount int DEFAULT 0 NULL,
	PricePerCustomer float DEFAULT 0 NULL,
	ConversionRate float DEFAULT 0 NULL,
	PV int DEFAULT 0 NULL,
	SnSGMV float DEFAULT 0 NULL,
	SnSCOGS float DEFAULT 0 NULL,
	SnSPercent float DEFAULT 0 NULL,
	SnSUnitsSold int DEFAULT 0 NULL,
	SnSReturnUnits int DEFAULT 0 NULL,
	ReviewCount int DEFAULT 0 NULL,
	AvgRating float DEFAULT 0 NULL,
	BoxID int NULL,
	BrandID int NULL,
	CollectedDate datetime DEFAULT getdate() NULL,
	CONSTRAINT PK_CoupangSales PRIMARY KEY (Idx),
	CONSTRAINT FK_CoupangSales_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID),
	CONSTRAINT FK_CoupangSales_ProductBox FOREIGN KEY (BoxID) REFERENCES oriodatabase.dbo.ProductBox(BoxID)
);
 CREATE NONCLUSTERED INDEX IX_CoupangSales_BoxID ON oriodatabase.dbo.CoupangSales (  BoxID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_CoupangSales_BrandID ON oriodatabase.dbo.CoupangSales (  BrandID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_CoupangSales_Date_Brand ON oriodatabase.dbo.CoupangSales (  Date ASC  , Brand ASC  )  
	 INCLUDE ( COGS , GMV , UnitsSold ) 
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_CoupangSales_Date_BrandID ON oriodatabase.dbo.CoupangSales (  Date ASC  , BrandID ASC  )  
	 INCLUDE ( COGS , GMV , UnitsSold ) 
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_CoupangSales_Date_SKUID ON oriodatabase.dbo.CoupangSales (  Date ASC  , SKUID ASC  )  
	 INCLUDE ( COGS , GMV , UnitsSold ) 
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.ERPSales definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.ERPSales;

CREATE TABLE oriodatabase.dbo.ERPSales (
	IDX int IDENTITY(1,1) NOT NULL,
	[DATE] datetime2 NOT NULL,
	BRAND nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ProductID int NULL,
	PRODUCT_NAME nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ERPCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Quantity decimal(18,2) NULL,
	UnitPrice decimal(18,2) NULL,
	TaxableAmount decimal(18,2) NULL,
	ChannelID int NULL,
	ChannelName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ChannelDetailID int NULL,
	ChannelDetailName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Owner nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CollectedDate datetime2 DEFAULT getdate() NOT NULL,
	BrandID int NULL,
	ERPIDX nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	DateNo nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	WarehouseID int NOT NULL,
	WarehouseName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	TransactionType nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	CONSTRAINT PK_ERPSales PRIMARY KEY (IDX),
	CONSTRAINT UC_ERPSales_ERPIDX UNIQUE (ERPIDX),
	CONSTRAINT FK_ERPSales_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID),
	CONSTRAINT FK_ERPSales_Channel FOREIGN KEY (ChannelID) REFERENCES oriodatabase.dbo.Channel(ChannelID),
	CONSTRAINT FK_ERPSales_ChannelDetail FOREIGN KEY (ChannelDetailID) REFERENCES oriodatabase.dbo.ChannelDetail(ChannelDetailID),
	CONSTRAINT FK_ERPSales_Product FOREIGN KEY (ProductID) REFERENCES oriodatabase.dbo.Product(ProductID),
	CONSTRAINT FK_ERPSales_Warehouse FOREIGN KEY (WarehouseID) REFERENCES oriodatabase.dbo.Warehouse(WarehouseID)
);
 CREATE NONCLUSTERED INDEX IX_ERPSales_BrandID ON oriodatabase.dbo.ERPSales (  BrandID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ERPSales_ChannelID ON oriodatabase.dbo.ERPSales (  ChannelID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ERPSales_Date ON oriodatabase.dbo.ERPSales (  DATE ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ERPSales_Date_Brand ON oriodatabase.dbo.ERPSales (  DATE ASC  , BrandID ASC  )  
	 INCLUDE ( Quantity , TaxableAmount ) 
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ERPSales_Date_Channel ON oriodatabase.dbo.ERPSales (  DATE ASC  , ChannelID ASC  )  
	 INCLUDE ( Quantity , TaxableAmount ) 
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ERPSales_Date_Product ON oriodatabase.dbo.ERPSales (  DATE ASC  , ProductID ASC  )  
	 INCLUDE ( Quantity , TaxableAmount ) 
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ERPSales_ProductID ON oriodatabase.dbo.ERPSales (  ProductID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.OrdersRealtime definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.OrdersRealtime;

CREATE TABLE oriodatabase.dbo.OrdersRealtime (
	OrderID int IDENTITY(1,1) NOT NULL,
	SourceChannel nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	SourceOrderID nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ContractType nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	OrderDate datetime2 NOT NULL,
	ChannelID int NULL,
	ProductID int NULL,
	CustomerName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	OrderQuantity int NOT NULL,
	OrderPrice decimal(18,2) NOT NULL,
	OrderAmountExVAT decimal(18,2) NULL,
	OrderStatus nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CollectedDate datetime2 DEFAULT getdate() NULL,
	UpdatedDate datetime2 DEFAULT getdate() NULL,
	BrandID int NULL,
	ShippedDate datetime2 NULL,
	SabangnetIDX int NULL,
	OrderAmountInVAT decimal(18,2) NULL,
	CONSTRAINT PK_OrdersRealtime PRIMARY KEY (OrderID),
	CONSTRAINT FK_OrdersRT_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID),
	CONSTRAINT FK_OrdersRT_Channel FOREIGN KEY (ChannelID) REFERENCES oriodatabase.dbo.Channel(ChannelID),
	CONSTRAINT FK_OrdersRT_Product FOREIGN KEY (ProductID) REFERENCES oriodatabase.dbo.Product(ProductID)
);
 CREATE NONCLUSTERED INDEX IX_OrdersRT_BrandID_Covering ON oriodatabase.dbo.OrdersRealtime (  BrandID ASC  , OrderDate ASC  )  
	 INCLUDE ( OrderAmountExVAT , OrderAmountInVAT , OrderPrice , OrderQuantity ) 
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_OrdersRT_ChannelID ON oriodatabase.dbo.OrdersRealtime (  ChannelID ASC  , OrderDate ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_OrdersRT_ProductID ON oriodatabase.dbo.OrdersRealtime (  ProductID ASC  , OrderDate ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_OrdersRT_SourceChannel ON oriodatabase.dbo.OrdersRealtime (  SourceChannel ASC  , OrderDate ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_OrdersRT_TransactionType ON oriodatabase.dbo.OrdersRealtime (  ContractType ASC  , OrderDate ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- oriodatabase.dbo.ProductBOM definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.ProductBOM;

CREATE TABLE oriodatabase.dbo.ProductBOM (
	BOMID int IDENTITY(1,1) NOT NULL,
	ParentProductBoxID int NOT NULL,
	ChildProductBoxID int NOT NULL,
	QuantityRequired decimal(10,2) NOT NULL,
	UpdatedDate datetime2 NULL,
	ParentProductID int NULL,
	ChildProductID int NULL,
	CONSTRAINT PK_ProductBOM PRIMARY KEY (BOMID),
	CONSTRAINT FK_ProductBOM_Child FOREIGN KEY (ChildProductBoxID) REFERENCES oriodatabase.dbo.ProductBox(BoxID),
	CONSTRAINT FK_ProductBOM_Parent FOREIGN KEY (ParentProductBoxID) REFERENCES oriodatabase.dbo.ProductBox(BoxID)
);
 CREATE NONCLUSTERED INDEX IX_ProductBOM_ChildBoxID ON oriodatabase.dbo.ProductBOM (  ChildProductBoxID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ProductBOM_ChildProductID ON oriodatabase.dbo.ProductBOM (  ChildProductID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ProductBOM_ParentBoxID ON oriodatabase.dbo.ProductBOM (  ParentProductBoxID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_ProductBOM_ParentProductID ON oriodatabase.dbo.ProductBOM (  ParentProductID ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;


-- dbo.vw_NaverAdWithCost_Frog source

-- ============================================
-- 5. View - Frog (BrandID = 0 가정)
-- ============================================
ALTER   VIEW vw_NaverAdWithCost_Frog AS
SELECT 
    ad.Idx,
    ad.Date,
    ad.CampaignID,
    ad.CampaignName,
    ad.AdGroupID,
    ad.AdGroupName,
    ad.KeywordID,
    ad.Keyword,
    ad.AdID,
    ad.AdName,
    ad.Device,
    ad.Impressions,
    ad.Clicks,
    ad.Conversions,
    ad.ConversionValue,
    ad.CollectedDate,
    ad.UpdatedDate,
    c.ContractName,
    ISNULL(c.TotalBudget / (DATEDIFF(day, c.StartDate, c.EndDate) + 1), 0) AS DailyBudget
FROM dbo.AdDataNaver_Frog ad
LEFT JOIN dbo.AdContractNaver c 
    ON ad.Date BETWEEN c.StartDate AND c.EndDate
    AND c.IsActive = 1
    AND c.BrandID = 0
    AND (c.CampaignID IS NULL OR c.CampaignID = ad.CampaignID);


-- dbo.vw_NaverAdWithCost_ScrubDaddy source

ALTER VIEW vw_NaverAdWithCost_ScrubDaddy AS
SELECT 
    ad.*,
    c.ContractName,
    c.AdGroupName AS ContractAdGroupName,
    ISNULL(
        c.TotalBudget / (DATEDIFF(day, c.StartDate, c.EndDate) + 1) 
        / COUNT(*) OVER (PARTITION BY ad.Date, ad.AdGroupID)
    , 0) AS DailyBudget
FROM dbo.AdDataNaver ad
LEFT JOIN dbo.AdContractNaver c 
    ON ad.Date BETWEEN c.StartDate AND c.EndDate
    AND c.IsActive = 1
    AND c.BrandID = 3
    AND c.AdGroupID = ad.AdGroupID;


-- dbo.vw_TargetAll source

ALTER VIEW dbo.vw_TargetAll AS
-- 정기 목표 - 단품
SELECT
    N'정기'                    AS 목표구분,
    tbp.[Date]                AS StartDate,
    tbp.[Date]                AS EndDate,
    tbp.BrandID,
    tbp.BrandName,
    tbp.ChannelID,
    tbp.ChannelName,
    tbp.UniqueCode            AS OriginalUniqueCode,
    tbp.ProductName           AS OriginalProductName,
    N'단품'                   AS SourceType,
    tbp.UniqueCode,
    tbp.ProductName,
    p.BaseBarcode,
    tbp.TargetQuantity,
    tbp.TargetQuantity        AS ComponentQuantity
FROM oriodatabase.dbo.TargetBaseProduct tbp
INNER JOIN oriodatabase.dbo.Product p ON tbp.UniqueCode = p.UniqueCode
WHERE NOT EXISTS (
    SELECT 1 FROM oriodatabase.dbo.ProductBOM bom
    WHERE bom.ParentProductID = p.ProductID
)
UNION ALL
-- 정기 목표 - 세트
SELECT
    N'정기',
    tbp.[Date],
    tbp.[Date],
    tbp.BrandID,
    tbp.BrandName,
    tbp.ChannelID,
    tbp.ChannelName,
    tbp.UniqueCode,
    tbp.ProductName,
    N'세트',
    cp.UniqueCode,
    cp.Name,
    cp.BaseBarcode,
    tbp.TargetQuantity,
    tbp.TargetQuantity * CAST(bom.QuantityRequired AS int)
FROM oriodatabase.dbo.TargetBaseProduct tbp
INNER JOIN oriodatabase.dbo.Product pp ON tbp.UniqueCode = pp.UniqueCode
INNER JOIN oriodatabase.dbo.ProductBOM bom ON bom.ParentProductID = pp.ProductID
INNER JOIN oriodatabase.dbo.Product cp ON bom.ChildProductID = cp.ProductID
UNION ALL
-- 비정기 목표 - 단품
SELECT
    N'비정기',
    tpp.StartDate,
    tpp.EndDate,
    tpp.BrandID,
    tpp.BrandName,
    tpp.ChannelID,
    tpp.ChannelName,
    tpp.UniqueCode,
    tpp.ProductName,
    N'단품',
    tpp.UniqueCode,
    tpp.ProductName,
    p.BaseBarcode,
    tpp.TargetQuantity,
    tpp.TargetQuantity
FROM oriodatabase.dbo.TargetPromotionProduct tpp
INNER JOIN oriodatabase.dbo.Product p ON tpp.UniqueCode = p.UniqueCode
WHERE NOT EXISTS (
    SELECT 1 FROM oriodatabase.dbo.ProductBOM bom
    WHERE bom.ParentProductID = p.ProductID
)
UNION ALL
-- 비정기 목표 - 세트
SELECT
    N'비정기',
    tpp.StartDate,
    tpp.EndDate,
    tpp.BrandID,
    tpp.BrandName,
    tpp.ChannelID,
    tpp.ChannelName,
    tpp.UniqueCode,
    tpp.ProductName,
    N'세트',
    cp.UniqueCode,
    cp.Name,
    cp.BaseBarcode,
    tpp.TargetQuantity,
    tpp.TargetQuantity * CAST(bom.QuantityRequired AS int)
FROM oriodatabase.dbo.TargetPromotionProduct tpp
INNER JOIN oriodatabase.dbo.Product pp ON tpp.UniqueCode = pp.UniqueCode
INNER JOIN oriodatabase.dbo.ProductBOM bom ON bom.ParentProductID = pp.ProductID
INNER JOIN oriodatabase.dbo.Product cp ON bom.ChildProductID = cp.ProductID;