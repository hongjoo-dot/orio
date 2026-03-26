-- ============================================
-- 쿠팡 재고 테이블
-- 원본: 쿠팡_3월_재고값 데이터.csv
-- 연결: SKU ID → ProductBox.CoupangSKU
-- ============================================

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
	CONSTRAINT FK_CoupangInventory_ProductBox FOREIGN KEY (BoxID) REFERENCES oriodatabase.dbo.ProductBox(BoxID),
	CONSTRAINT FK_CoupangInventory_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID)
);
CREATE NONCLUSTERED INDEX IX_CoupangInventory_Date_SKUID ON oriodatabase.dbo.CoupangInventory ([Date] ASC, SKUID ASC)
	WITH (PAD_INDEX = OFF, FILLFACTOR = 100, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, STATISTICS_NORECOMPUTE = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)
	ON [PRIMARY];
CREATE NONCLUSTERED INDEX IX_CoupangInventory_BoxID ON oriodatabase.dbo.CoupangInventory (BoxID ASC)
	WITH (PAD_INDEX = OFF, FILLFACTOR = 100, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, STATISTICS_NORECOMPUTE = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)
	ON [PRIMARY];
CREATE NONCLUSTERED INDEX IX_CoupangInventory_BrandID ON oriodatabase.dbo.CoupangInventory (BrandID ASC)
	WITH (PAD_INDEX = OFF, FILLFACTOR = 100, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, STATISTICS_NORECOMPUTE = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)
	ON [PRIMARY];


-- ============================================
-- 쿠팡 판매 테이블
-- 원본: 쿠팡_26년 판매수량 자료 3월 마감.xlsx (RAW DATA 시트)
-- 연결: SKU ID → ProductBox.CoupangSKU
-- ============================================

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
	CONSTRAINT FK_CoupangSales_ProductBox FOREIGN KEY (BoxID) REFERENCES oriodatabase.dbo.ProductBox(BoxID),
	CONSTRAINT FK_CoupangSales_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID)
);
CREATE NONCLUSTERED INDEX IX_CoupangSales_Date_SKUID ON oriodatabase.dbo.CoupangSales ([Date] ASC, SKUID ASC)
	INCLUDE (GMV, UnitsSold, COGS)
	WITH (PAD_INDEX = OFF, FILLFACTOR = 100, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, STATISTICS_NORECOMPUTE = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)
	ON [PRIMARY];
CREATE NONCLUSTERED INDEX IX_CoupangSales_BoxID ON oriodatabase.dbo.CoupangSales (BoxID ASC)
	WITH (PAD_INDEX = OFF, FILLFACTOR = 100, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, STATISTICS_NORECOMPUTE = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)
	ON [PRIMARY];
CREATE NONCLUSTERED INDEX IX_CoupangSales_BrandID ON oriodatabase.dbo.CoupangSales (BrandID ASC)
	WITH (PAD_INDEX = OFF, FILLFACTOR = 100, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, STATISTICS_NORECOMPUTE = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)
	ON [PRIMARY];
CREATE NONCLUSTERED INDEX IX_CoupangSales_Date_BrandID ON oriodatabase.dbo.CoupangSales ([Date] ASC, BrandID ASC)
	INCLUDE (GMV, UnitsSold, COGS)
	WITH (PAD_INDEX = OFF, FILLFACTOR = 100, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, STATISTICS_NORECOMPUTE = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)
	ON [PRIMARY];
CREATE NONCLUSTERED INDEX IX_CoupangSales_Date_Brand ON oriodatabase.dbo.CoupangSales ([Date] ASC, Brand ASC)
	INCLUDE (GMV, UnitsSold, COGS)
	WITH (PAD_INDEX = OFF, FILLFACTOR = 100, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, STATISTICS_NORECOMPUTE = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)
	ON [PRIMARY];