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
	CONSTRAINT PK_AdDataMeta PRIMARY KEY (Idx)
);
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


-- oriodatabase.dbo.Brand definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Brand;

CREATE TABLE oriodatabase.dbo.Brand (
	BrandID int IDENTITY(1,1) NOT NULL,
	Name nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	UpdatedDate datetime2 DEFAULT getdate() NULL,
	Title nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsActive bit DEFAULT 1 NOT NULL,
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
	use_blacklist nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	blacklist_type nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	authentication_method nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	sms nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	news_mail nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	gender nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	solar_calendar nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	total_points decimal(18,2) NULL,
	available_points decimal(18,2) NULL,
	used_points decimal(18,2) NULL,
	available_credits decimal(18,2) NULL,
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
 CREATE NONCLUSTERED INDEX IX_Cafe24Orders_shipping_status ON oriodatabase.dbo.Cafe24Orders (  shipping_status ASC  )  
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


-- oriodatabase.dbo.Warehouse definition

-- Drop table

-- DROP TABLE oriodatabase.dbo.Warehouse;

CREATE TABLE oriodatabase.dbo.Warehouse (
	WarehouseID int IDENTITY(1,1) NOT NULL,
	WarehouseName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	CONSTRAINT PK_Warehouse PRIMARY KEY (WarehouseID),
	CONSTRAINT UQ_Warehouse_Name UNIQUE (WarehouseName)
);


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
	ProductType nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK_Product PRIMARY KEY (ProductID),
	CONSTRAINT FK_Product_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID)
);
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
	CONSTRAINT PK_ProductBox PRIMARY KEY (BoxID),
	CONSTRAINT FK_ProductBox_Product FOREIGN KEY (ProductID) REFERENCES oriodatabase.dbo.Product(ProductID)
);
 CREATE UNIQUE NONCLUSTERED INDEX UQ_ProductBox_ERPCode ON oriodatabase.dbo.ProductBox (  ERPCode ASC  )  
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
 CREATE NONCLUSTERED INDEX IX_SabangnetOrders_OrderDate ON oriodatabase.dbo.SabangnetOrders (  ORDER_DATE ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_SabangnetOrders_OrderID ON oriodatabase.dbo.SabangnetOrders (  ORDER_ID ASC  )  
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
	OrderAmount decimal(18,2) NULL,
	OrderStatus nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CollectedDate datetime2 DEFAULT getdate() NULL,
	UpdatedDate datetime2 DEFAULT getdate() NULL,
	BrandID int NULL,
	ShippedDate datetime2 NULL,
	SabangnetIDX int NULL,
	CONSTRAINT PK_OrdersRealtime PRIMARY KEY (OrderID),
	CONSTRAINT FK_OrdersRT_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID),
	CONSTRAINT FK_OrdersRT_Channel FOREIGN KEY (ChannelID) REFERENCES oriodatabase.dbo.Channel(ChannelID),
	CONSTRAINT FK_OrdersRT_Product FOREIGN KEY (ProductID) REFERENCES oriodatabase.dbo.Product(ProductID)
);
 CREATE NONCLUSTERED INDEX IX_OrdersRT_BrandID ON oriodatabase.dbo.OrdersRealtime (  BrandID ASC  , OrderDate ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_OrdersRT_ChannelID ON oriodatabase.dbo.OrdersRealtime (  ChannelID ASC  , OrderDate ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;
 CREATE NONCLUSTERED INDEX IX_OrdersRT_ProductID ON oriodatabase.dbo.OrdersRealtime (  ProductID ASC  , OrderDate ASC  )  
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


-- ============================================
-- 광고비 계약 테이블 (통합 - 1개)
-- ============================================
CREATE TABLE dbo.AdContractNaver (
    ContractID int IDENTITY(1,1) PRIMARY KEY,
    ContractName nvarchar(200) NOT NULL,
    BrandID int NULL,
    CampaignID nvarchar(50) NULL,
    StartDate date NOT NULL,
    EndDate date NOT NULL,
    TotalBudget decimal(18,2) NOT NULL,
    IsActive bit DEFAULT 1,
    CreatedDate datetime DEFAULT GETDATE(),
    UpdatedDate datetime DEFAULT GETDATE(),
    
    CONSTRAINT FK_AdContractNaver_Brand FOREIGN KEY (BrandID) 
        REFERENCES dbo.Brand(BrandID)
);

CREATE NONCLUSTERED INDEX IX_AdContractNaver_Dates 
    ON dbo.AdContractNaver (StartDate, EndDate);
CREATE NONCLUSTERED INDEX IX_AdContractNaver_BrandID 
    ON dbo.AdContractNaver (BrandID);


-- ============================================
-- 광고 데이터 테이블 - Frog
-- ============================================
CREATE TABLE dbo.AdDataNaver_Frog (
    Idx bigint IDENTITY(1,1) NOT NULL,
    [Date] date NOT NULL,
    CampaignID nvarchar(50) NULL,
    CampaignName nvarchar(200) NULL,
    AdGroupID nvarchar(50) NULL,
    AdGroupName nvarchar(200) NULL,
    KeywordID nvarchar(50) NULL,
    Keyword nvarchar(200) NULL,
    AdID nvarchar(50) NOT NULL,
    AdName nvarchar(200) NULL,
    Device nvarchar(20) NULL,
    Impressions int DEFAULT 0 NULL,
    Clicks int DEFAULT 0 NULL,
    Conversions int DEFAULT 0 NULL,
    ConversionValue float DEFAULT 0 NULL,
    CollectedDate datetime DEFAULT GETDATE() NULL,
    UpdatedDate datetime DEFAULT GETDATE() NULL,
    CONSTRAINT PK_AdDataNaver_Frog PRIMARY KEY (Idx)
);

CREATE NONCLUSTERED INDEX IX_AdDataNaver_Frog_Date_AdID 
    ON dbo.AdDataNaver_Frog ([Date], AdID, KeywordID, Device);
GO

-- ============================================
-- View - ScrubDaddy (BrandID = 3)
-- ============================================
CREATE OR ALTER VIEW vw_NaverAdWithCost_ScrubDaddy AS
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
FROM dbo.AdDataNaver ad
LEFT JOIN dbo.AdContractNaver c 
    ON ad.Date BETWEEN c.StartDate AND c.EndDate
    AND c.IsActive = 1
    AND c.BrandID = 3
    AND (c.CampaignID IS NULL OR c.CampaignID = ad.CampaignID);
GO

-- ============================================
-- View - Frog (BrandID = 0)
-- ============================================
CREATE OR ALTER VIEW vw_NaverAdWithCost_Frog AS
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
GO