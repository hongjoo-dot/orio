"""
RevenuePlan 초기 데이터 업로드 스크립트
- Excel 파일에서 TARGET_REVENUE, EXPECTED_REVENUE 시트를 읽어 DB에 업로드
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime

# DB 연결
from core import get_db_cursor


def create_table_if_not_exists():
    """RevenuePlan 테이블 생성"""
    print("\n[1] RevenuePlan 테이블 확인/생성")

    with get_db_cursor(commit=True) as cursor:
        # 테이블 존재 여부 확인
        cursor.execute("""
            SELECT COUNT(*) FROM sys.tables WHERE name = 'RevenuePlan'
        """)
        exists = cursor.fetchone()[0] > 0

        if exists:
            print("   테이블이 이미 존재합니다.")
            return True

        # 테이블 생성
        cursor.execute("""
            CREATE TABLE [dbo].[RevenuePlan] (
                [PlanID]        INT IDENTITY(1,1) PRIMARY KEY,
                [Date]          DATE NOT NULL,
                [BrandID]       INT NOT NULL,
                [ChannelID]     INT NOT NULL,
                [PlanType]      NVARCHAR(20) NOT NULL,
                [Amount]        DECIMAL(18,2) NOT NULL DEFAULT 0,
                [CreatedAt]     DATETIME2 DEFAULT GETDATE(),
                [UpdatedAt]     DATETIME2 DEFAULT GETDATE(),
                CONSTRAINT [FK_RevenuePlan_Brand] FOREIGN KEY ([BrandID])
                    REFERENCES [dbo].[Brand]([BrandID]),
                CONSTRAINT [FK_RevenuePlan_Channel] FOREIGN KEY ([ChannelID])
                    REFERENCES [dbo].[Channel]([ChannelID]),
                CONSTRAINT [CK_RevenuePlan_PlanType] CHECK ([PlanType] IN ('TARGET', 'EXPECTED'))
            )
        """)
        print("   테이블 생성 완료")

        # 인덱스 생성
        cursor.execute("""
            CREATE INDEX [IX_RevenuePlan_Date_Brand_Channel]
            ON [dbo].[RevenuePlan] ([Date], [BrandID], [ChannelID], [PlanType])
        """)

        cursor.execute("""
            CREATE UNIQUE INDEX [UQ_RevenuePlan_Unique]
            ON [dbo].[RevenuePlan] ([Date], [BrandID], [ChannelID], [PlanType])
        """)
        print("   인덱스 생성 완료")

        return True


def load_mappings():
    """Brand, Channel 매핑 테이블 로드"""
    print("\n[2] 매핑 테이블 로드")

    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT Name, BrandID FROM [dbo].[Brand]")
        brand_map = {row[0]: row[1] for row in cursor.fetchall()}
        print(f"   Brand: {len(brand_map)}개")

        cursor.execute("SELECT Name, ChannelID FROM [dbo].[Channel]")
        channel_map = {row[0]: row[1] for row in cursor.fetchall()}
        print(f"   Channel: {len(channel_map)}개")

    return brand_map, channel_map


def upload_sheet(df, plan_type, brand_map, channel_map):
    """시트 데이터 업로드"""
    print(f"\n[3] {plan_type} 데이터 업로드")
    print(f"   총 {len(df):,}행")

    # 컬럼명 정규화
    df.columns = [col.upper().strip() for col in df.columns]

    # 날짜 변환
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    df = df[df['DATE'].notna()]

    # 매핑 및 집계
    unmapped_brands = set()
    unmapped_channels = set()
    aggregated_data = {}

    for idx, row in df.iterrows():
        brand_name = str(row['BRAND']).strip() if pd.notna(row['BRAND']) else None
        channel_name = str(row['CHANNEL']).strip() if pd.notna(row['CHANNEL']) else None

        brand_id = brand_map.get(brand_name)
        channel_id = channel_map.get(channel_name)

        if brand_name and brand_id is None:
            unmapped_brands.add(brand_name)
            continue

        if channel_name and channel_id is None:
            unmapped_channels.add(channel_name)
            continue

        if brand_id is None or channel_id is None:
            continue

        # 금액 컬럼 찾기
        amount_col = 'TARGET_REVENUE' if 'TARGET_REVENUE' in df.columns else 'EXPECTED_REVENUE'
        amount = float(row[amount_col]) if pd.notna(row.get(amount_col)) else 0

        # 키 생성 (Date, BrandID, ChannelID, PlanType)
        date_key = row['DATE'].date() if hasattr(row['DATE'], 'date') else row['DATE']
        key = (date_key, brand_id, channel_id, plan_type)
        
        aggregated_data[key] = aggregated_data.get(key, 0) + amount

    # 집계된 데이터를 records 리스트로 변환
    records = []
    for key, amount in aggregated_data.items():
        records.append({
            'Date': key[0],
            'BrandID': key[1],
            'ChannelID': key[2],
            'PlanType': key[3],
            'Amount': amount
        })

    print(f"   유효 레코드 (집계 후): {len(records):,}건 (원본: {len(df):,}행)")

    if unmapped_brands:
        print(f"   [경고] 매핑 안 된 브랜드: {sorted(unmapped_brands)}")
    if unmapped_channels:
        print(f"   [경고] 매핑 안 된 채널: {sorted(unmapped_channels)}")

    # UPSERT
    inserted = 0
    updated = 0

    merge_sql = """
        MERGE INTO [dbo].[RevenuePlan] AS target
        USING (SELECT ? AS [Date], ? AS BrandID, ? AS ChannelID, ? AS PlanType) AS source
        ON target.[Date] = source.[Date]
           AND target.BrandID = source.BrandID
           AND target.ChannelID = source.ChannelID
           AND target.PlanType = source.PlanType
        WHEN MATCHED THEN
            UPDATE SET
                Amount = ?,
                UpdatedAt = GETDATE()
        WHEN NOT MATCHED THEN
            INSERT ([Date], BrandID, ChannelID, PlanType, Amount, CreatedAt, UpdatedAt)
            VALUES (?, ?, ?, ?, ?, GETDATE(), GETDATE())
        OUTPUT $action;
    """

    with get_db_cursor(commit=True) as cursor:
        for i, record in enumerate(records):
            cursor.execute(merge_sql, (
                record['Date'], record['BrandID'], record['ChannelID'], record['PlanType'],
                record['Amount'],
                record['Date'], record['BrandID'], record['ChannelID'], record['PlanType'], record['Amount']
            ))

            result = cursor.fetchone()
            if result and result[0] == 'INSERT':
                inserted += 1
            elif result and result[0] == 'UPDATE':
                updated += 1

            if (i + 1) % 100 == 0:
                print(f"   진행: {i + 1}/{len(records)}")

    print(f"   완료: INSERT {inserted:,}건, UPDATE {updated:,}건")
    return inserted, updated


def main():
    excel_path = r"C:\Python\[DATA] ORIO_DATABASE_PowerBI_Upload.xlsx"

    print("=" * 60)
    print("RevenuePlan 데이터 업로드")
    print("=" * 60)
    print(f"파일: {excel_path}")

    # 1. 테이블 생성
    create_table_if_not_exists()

    # 2. 매핑 로드
    brand_map, channel_map = load_mappings()

    # 3. Excel 읽기
    print("\n[3] Excel 파일 읽기")
    xl = pd.ExcelFile(excel_path)
    print(f"   시트: {xl.sheet_names}")

    total_inserted = 0
    total_updated = 0

    # TARGET_REVENUE
    if 'TARGET_REVENUE' in xl.sheet_names:
        df_target = pd.read_excel(excel_path, sheet_name='TARGET_REVENUE')
        ins, upd = upload_sheet(df_target, 'TARGET', brand_map, channel_map)
        total_inserted += ins
        total_updated += upd

    # EXPECTED_REVENUE
    if 'EXPECTED_REVENUE' in xl.sheet_names:
        df_expected = pd.read_excel(excel_path, sheet_name='EXPECTED_REVENUE')
        ins, upd = upload_sheet(df_expected, 'EXPECTED', brand_map, channel_map)
        total_inserted += ins
        total_updated += upd

    print("\n" + "=" * 60)
    print(f"총 결과: INSERT {total_inserted:,}건, UPDATE {total_updated:,}건")
    print("=" * 60)


if __name__ == "__main__":
    main()
