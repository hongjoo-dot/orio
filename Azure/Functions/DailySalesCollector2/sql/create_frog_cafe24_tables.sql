-- ============================================================
-- Frog Cafe24 테이블 생성 + SystemConfig 등록
-- 프로그 자사몰 (frogstore01) 데이터 파이프라인용
-- ============================================================

-- 1. FrogCafe24Orders (주문 마스터)
CREATE TABLE FrogCafe24Orders (
    Cafe24OrderID INT IDENTITY(1,1) PRIMARY KEY,
    order_id NVARCHAR(100) NOT NULL,
    order_date DATETIME,
    payment_date DATETIME,
    order_status NVARCHAR(50),
    shipping_status NVARCHAR(50),
    shipped_date DATETIME,
    purchaseconfirmation_date DATETIME,
    member_id NVARCHAR(100),
    billing_name NVARCHAR(200),
    member_email NVARCHAR(200),
    order_place_name NVARCHAR(200),
    order_from_mobile BIT,
    order_price_amount DECIMAL(18,2),
    shipping_fee DECIMAL(18,2),
    coupon_discount_price DECIMAL(18,2),
    points_spent_amount DECIMAL(18,2),
    payment_amount DECIMAL(18,2),
    payment_method NVARCHAR(200),
    payment_gateway_names NVARCHAR(200),
    paid BIT,
    canceled BIT,
    cancel_date DATETIME,
    first_order BIT,
    CollectedDate DATETIME DEFAULT GETDATE()
);

CREATE UNIQUE INDEX UX_FrogCafe24Orders_order_id ON FrogCafe24Orders(order_id);

-- 2. FrogCafe24OrdersDetail (주문 상세)
CREATE TABLE FrogCafe24OrdersDetail (
    DetailID INT IDENTITY(1,1) PRIMARY KEY,
    Cafe24OrderID INT,
    order_id NVARCHAR(100),
    order_item_code NVARCHAR(100) NOT NULL,
    item_no INT,
    ProductUniqueCode NVARCHAR(100),
    ProductID INT,
    custom_product_code NVARCHAR(100),
    custom_variant_code NVARCHAR(100),
    product_name NVARCHAR(500),
    option_value NVARCHAR(500),
    quantity INT,
    product_price DECIMAL(18,2),
    payment_amount DECIMAL(18,2),
    coupon_discount_price DECIMAL(18,2),
    order_status NVARCHAR(50),
    order_status_additional_info NVARCHAR(500),
    shipping_code NVARCHAR(100),
    shipping_company_name NVARCHAR(200),
    tracking_no NVARCHAR(100),
    product_bundle BIT,
    supplier_id NVARCHAR(100),
    made_in_code NVARCHAR(50),
    CollectedDate DATETIME DEFAULT GETDATE()
);

CREATE UNIQUE INDEX UX_FrogCafe24OrdersDetail_order_item_code ON FrogCafe24OrdersDetail(order_item_code);

-- 3. FrogCafe24Customers (고객 마스터)
CREATE TABLE FrogCafe24Customers (
    CustomerID INT IDENTITY(1,1) PRIMARY KEY,
    member_id NVARCHAR(100) NOT NULL,
    shop_no INT,
    group_no INT,
    phone NVARCHAR(50),
    cellphone NVARCHAR(50),
    member_authentication BIT,
    authentication_method NVARCHAR(50),
    sms BIT,
    news_mail BIT,
    gender NVARCHAR(10),
    total_points INT,
    available_points INT,
    used_points INT,
    use_mobile_app BIT,
    fixed_group BIT,
    last_login_date DATETIME,
    created_date DATETIME,
    next_grade NVARCHAR(100),
    total_purchase_amount DECIMAL(18,2),
    total_purchase_count INT,
    required_purchase_amount DECIMAL(18,2),
    required_purchase_count INT,
    CollectedDate DATETIME DEFAULT GETDATE()
);

CREATE UNIQUE INDEX UX_FrogCafe24Customers_member_id ON FrogCafe24Customers(member_id);

-- ============================================================
-- 4. SystemConfig 등록
-- ============================================================
INSERT INTO SystemConfig (Category, ConfigKey, ConfigValue, DataType, IsActive)
VALUES
    ('FrogCafe24', 'MALL_ID', 'frogstore01', 'string', 1),
    ('FrogCafe24', 'CLIENT_ID', 'jYJYuHUrEtolg5egal8FRD', 'string', 1),
    ('FrogCafe24', 'CLIENT_SECRET', 'arf40GUJLCbdjTbQlsKsLB', 'string', 1),
    ('FrogCafe24', 'ACCESS_TOKEN', '9kUgqOIBOxUiBq6gE4LTRC', 'string', 1),
    ('FrogCafe24', 'REFRESH_TOKEN', 'eX9YHeeU6I1VN2h3TpDUPR', 'string', 1),
    ('FrogCafe24', 'API_VERSION', '2025-12-01', 'string', 1),
    ('FrogCafe24', 'ROLLING_DAYS', '10', 'int', 1),
    ('FrogCafe24', 'TOKEN_EXPIRES_AT', '', 'string', 1),
    ('FrogCafe24', 'REFRESH_TOKEN_EXPIRES_AT', '', 'string', 1);