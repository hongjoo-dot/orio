"""
AdDataMeta 테이블의 ImageURL, LinkURL 백필 스크립트
- DB에서 ImageURL 또는 LinkURL이 비어있는 고유 AdID 조회
- Meta API로 creative 정보 수집
- MERGE로 해당 필드만 업데이트 (중복 방지, 리소스 절약)
"""

import sys
import os
import json

# 환경 변수 로드
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

settings_path = os.path.join(current_dir, 'local.settings.json')
if os.path.exists(settings_path):
    with open(settings_path, 'r') as f:
        settings = json.load(f)
        for key, value in settings.get('Values', {}).items():
            if not key.startswith('COMMENT'):
                os.environ[key] = value
    print("[OK] local.settings.json 환경 변수 로드 완료")

from shared.meta.auth import MetaAPIAuth
from shared.meta.data_fetcher import MetaDataFetcher
from shared.database import get_db_connection
from shared.system_config import get_config


def get_ads_missing_urls():
    """DB에서 URL이 비어있는 고유 AdID 목록 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ImageURL, LinkURL, PreviewURL 중 하나라도 누락된 AdID 조회
        cursor.execute("""
            SELECT DISTINCT AdID
            FROM [dbo].[AdDataMeta]
            WHERE (ImageURL IS NULL OR ImageURL = '' OR ImageURL = ThumbnailURL)
               OR (LinkURL IS NULL OR LinkURL = '')
               OR (PreviewURL IS NULL OR PreviewURL = '')
        """)

        ad_ids = [row[0] for row in cursor.fetchall()]
        print(f"[DB] URL이 누락된 광고 수: {len(ad_ids)}개")
        return ad_ids

    finally:
        cursor.close()
        conn.close()


def get_current_url_status():
    """현재 URL 상태 통계 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                COUNT(DISTINCT AdID) as TotalAds,
                COUNT(DISTINCT CASE WHEN ImageURL IS NOT NULL AND ImageURL != '' AND ImageURL != ThumbnailURL THEN AdID END) as HasImageURL,
                COUNT(DISTINCT CASE WHEN LinkURL IS NOT NULL AND LinkURL != '' THEN AdID END) as HasLinkURL,
                COUNT(DISTINCT CASE WHEN ThumbnailURL IS NOT NULL AND ThumbnailURL != '' THEN AdID END) as HasThumbnailURL,
                COUNT(DISTINCT CASE WHEN PreviewURL IS NOT NULL AND PreviewURL != '' THEN AdID END) as HasPreviewURL
            FROM [dbo].[AdDataMeta]
        """)

        row = cursor.fetchone()
        return {
            'total_ads': row[0],
            'has_image_url': row[1],
            'has_link_url': row[2],
            'has_thumbnail_url': row[3],
            'has_preview_url': row[4]
        }

    finally:
        cursor.close()
        conn.close()


def update_creative_urls(creatives_map: dict):
    """크리에이티브 URL 정보를 DB에 업데이트 (MERGE 사용)"""
    if not creatives_map:
        print("[DB] 업데이트할 데이터 없음")
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 임시 테이블 생성
        cursor.execute("""
            CREATE TABLE #TempCreativeURLs (
                [AdID] [nvarchar](50),
                [ImageURL] [nvarchar](max),
                [LinkURL] [nvarchar](max),
                [PreviewURL] [nvarchar](max)
            )
        """)

        # 데이터 삽입
        data_to_insert = []
        for ad_id, creative in creatives_map.items():
            image_url = creative.get('image_url', '')
            link_url = creative.get('link_url', '')
            preview_url = creative.get('preview_url', '')

            # 값이 있는 경우만 추가
            if image_url or link_url or preview_url:
                data_to_insert.append((ad_id, image_url, link_url, preview_url))

        if not data_to_insert:
            print("[DB] 유효한 URL 데이터 없음")
            return 0

        cursor.executemany(
            "INSERT INTO #TempCreativeURLs VALUES (?, ?, ?, ?)",
            data_to_insert
        )

        # MERGE: ImageURL, LinkURL, PreviewURL 업데이트 (기존 데이터 보존)
        merge_query = """
            MERGE INTO [dbo].[AdDataMeta] AS target
            USING #TempCreativeURLs AS source
            ON target.AdID = source.AdID

            WHEN MATCHED AND (
                (source.ImageURL != '' AND (target.ImageURL IS NULL OR target.ImageURL = '' OR target.ImageURL = target.ThumbnailURL))
                OR
                (source.LinkURL != '' AND (target.LinkURL IS NULL OR target.LinkURL = ''))
                OR
                (source.PreviewURL != '' AND (target.PreviewURL IS NULL OR target.PreviewURL = ''))
            ) THEN
                UPDATE SET
                    ImageURL = CASE
                        WHEN source.ImageURL != '' AND (target.ImageURL IS NULL OR target.ImageURL = '' OR target.ImageURL = target.ThumbnailURL)
                        THEN source.ImageURL
                        ELSE target.ImageURL
                    END,
                    LinkURL = CASE
                        WHEN source.LinkURL != '' AND (target.LinkURL IS NULL OR target.LinkURL = '')
                        THEN source.LinkURL
                        ELSE target.LinkURL
                    END,
                    PreviewURL = CASE
                        WHEN source.PreviewURL != '' AND (target.PreviewURL IS NULL OR target.PreviewURL = '')
                        THEN source.PreviewURL
                        ELSE target.PreviewURL
                    END,
                    UpdatedDate = GETDATE();
        """
        cursor.execute(merge_query)

        affected_rows = cursor.rowcount
        conn.commit()
        print(f"[DB] {affected_rows}개 레코드 업데이트 완료")
        return affected_rows

    except Exception as e:
        print(f"[ERROR] DB 업데이트 실패: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def backfill_creative_urls():
    """메인 백필 로직"""
    print("=" * 60)
    print("AdDataMeta URL 백필 시작")
    print("=" * 60)

    # 1. 현재 상태 확인
    print("\n[1] 현재 상태 확인")
    print("-" * 40)
    status = get_current_url_status()
    print(f"총 광고 수: {status['total_ads']}")
    print(f"ImageURL 있음: {status['has_image_url']} ({status['has_image_url']/status['total_ads']*100:.1f}%)")
    print(f"LinkURL 있음: {status['has_link_url']} ({status['has_link_url']/status['total_ads']*100:.1f}%)")
    print(f"PreviewURL 있음: {status['has_preview_url']} ({status['has_preview_url']/status['total_ads']*100:.1f}%)")

    # 2. 누락된 AdID 조회
    print("\n[2] 누락된 AdID 조회")
    print("-" * 40)
    missing_ad_ids = get_ads_missing_urls()

    if not missing_ad_ids:
        print("모든 광고에 URL이 채워져 있습니다!")
        return

    # 3. Meta API로 creative 정보 수집
    print("\n[3] Meta API 크리에이티브 수집")
    print("-" * 40)

    config = get_config()
    ad_accounts_json = config.get('MetaAdAPI', 'AD_ACCOUNTS')
    ad_accounts = json.loads(ad_accounts_json)

    auth = MetaAPIAuth()
    auth.refresh_long_lived_token()
    fetcher = MetaDataFetcher(auth.get_current_token())

    # 모든 계정에서 크리에이티브 수집
    all_creatives = {}
    for account in ad_accounts:
        print(f"  계정: {account['name']}...")
        creatives = fetcher.fetch_ad_creatives(account['id'])
        all_creatives.update(creatives)

    print(f"  총 {len(all_creatives)}개 크리에이티브 수집")

    # 4. 누락된 AdID에 해당하는 크리에이티브만 필터링
    print("\n[4] 누락된 광고 필터링")
    print("-" * 40)

    missing_ad_ids_set = set(missing_ad_ids)
    filtered_creatives = {
        ad_id: creative
        for ad_id, creative in all_creatives.items()
        if ad_id in missing_ad_ids_set
    }

    print(f"  매칭된 광고 수: {len(filtered_creatives)}개")

    # URL이 있는 것만 필터링
    valid_creatives = {
        ad_id: creative
        for ad_id, creative in filtered_creatives.items()
        if creative.get('image_url') or creative.get('link_url') or creative.get('preview_url')
    }

    print(f"  유효한 URL 있는 광고 수: {len(valid_creatives)}개")

    # 5. DB 업데이트
    print("\n[5] DB 업데이트 (MERGE)")
    print("-" * 40)
    updated_count = update_creative_urls(valid_creatives)

    # 6. 결과 확인
    print("\n[6] 최종 결과")
    print("-" * 40)
    final_status = get_current_url_status()
    print(f"총 광고 수: {final_status['total_ads']}")
    print(f"ImageURL 있음: {final_status['has_image_url']} ({final_status['has_image_url']/final_status['total_ads']*100:.1f}%)")
    print(f"LinkURL 있음: {final_status['has_link_url']} ({final_status['has_link_url']/final_status['total_ads']*100:.1f}%)")
    print(f"PreviewURL 있음: {final_status['has_preview_url']} ({final_status['has_preview_url']/final_status['total_ads']*100:.1f}%)")

    # 개선율 계산
    image_improvement = final_status['has_image_url'] - status['has_image_url']
    link_improvement = final_status['has_link_url'] - status['has_link_url']
    preview_improvement = final_status['has_preview_url'] - status['has_preview_url']

    print("\n" + "=" * 60)
    print("백필 완료!")
    print(f"ImageURL 개선: +{image_improvement}개")
    print(f"LinkURL 개선: +{link_improvement}개")
    print(f"PreviewURL 개선: +{preview_improvement}개")
    print("=" * 60)


if __name__ == '__main__':
    backfill_creative_urls()
