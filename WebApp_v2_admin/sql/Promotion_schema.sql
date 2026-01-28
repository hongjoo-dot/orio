CREATE TABLE oriodatabase.dbo.Promotion (
	PromotionID nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	PromotionName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	PromotionType nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	StartDate date NOT NULL,
	StartTime time DEFAULT '00:00:00' NOT NULL,
	EndDate date NOT NULL,
	EndTime time DEFAULT '00:00:00' NOT NULL,
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
	CONSTRAINT PK__Promotio__52C42F2FB81831C0 PRIMARY KEY (PromotionID)
);


-- oriodatabase.dbo.Promotion foreign keys

ALTER TABLE oriodatabase.dbo.Promotion ADD CONSTRAINT FK_Promotion_Brand FOREIGN KEY (BrandID) REFERENCES oriodatabase.dbo.Brand(BrandID);



CREATE TABLE oriodatabase.dbo.PromotionProduct (
	PromotionProductID int IDENTITY(1,1) NOT NULL,
	PromotionID nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	UniqueCode nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ProductName nvarchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SellingPrice decimal(18,2) NULL,
	PromotionPrice decimal(18,2) NULL,
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
	CONSTRAINT PK__Promotio__C7B85D3CBB631920 PRIMARY KEY (PromotionProductID),
	CONSTRAINT UQ_PromotionProduct UNIQUE (PromotionID,UniqueCode)
);


-- oriodatabase.dbo.PromotionProduct foreign keys

ALTER TABLE oriodatabase.dbo.PromotionProduct ADD CONSTRAINT FK_PromotionProduct_Promotion FOREIGN KEY (PromotionID) REFERENCES oriodatabase.dbo.Promotion(PromotionID);


CREATE TABLE oriodatabase.dbo.PromotionType (
	TypeCode nvarchar(5) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	TypeName nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	DisplayName nvarchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Category nvarchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	CONSTRAINT PK__Promotio__3E1CDC7D5A999E83 PRIMARY KEY (TypeCode)
);