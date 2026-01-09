"""
Meta API Raw 데이터 수집 모듈
"""

import requests
import time
from typing import List, Dict, Optional

class MetaDataFetcher:
    """Meta Ads Raw 데이터 수집기"""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://graph.facebook.com/v19.0"

    def fetch_insights_raw(
        self,
        ad_account_id: str,
        fields: List[str],
        level: str = 'ad',
        time_range: Optional[Dict] = None,
        filtering: Optional[List[Dict]] = None,
        breakdowns: Optional[List[str]] = None,
        action_breakdowns: Optional[List[str]] = None,
        time_increment: Optional[int] = None
    ) -> List[Dict]:
        """Meta Insights API에서 Raw 데이터 수집"""
        
        url = f"{self.base_url}/{ad_account_id}/insights"
        
        params = {
            'access_token': self.access_token,
            'fields': ','.join(fields),
            'level': level
        }

        if time_range:
            params['time_range'] = str(time_range).replace("'", '"')
        if time_increment is not None:
            params['time_increment'] = time_increment
        if filtering:
            params['filtering'] = str(filtering).replace("'", '"')
        if breakdowns:
            params['breakdowns'] = ','.join(breakdowns)
        if action_breakdowns:
            params['action_breakdowns'] = ','.join(action_breakdowns)

        all_data = []
        next_url = None
        max_retries = 3
        retry_delay = 5

        while True:
            retry_count = 0
            success = False

            while retry_count < max_retries and not success:
                try:
                    if next_url:
                        response = requests.get(next_url, timeout=30)
                    else:
                        response = requests.get(url, params=params, timeout=30)

                    response.raise_for_status()
                    json_data = response.json()

                    if 'data' in json_data:
                        all_data.extend(json_data['data'])

                    if 'paging' in json_data and 'next' in json_data['paging']:
                        next_url = json_data['paging']['next']
                    else:
                        next_url = None

                    success = True

                except requests.exceptions.HTTPError as e:
                    if e.response.status_code in [403, 429]:
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"[WARNING] Rate Limit 감지. {retry_delay}초 후 재시도...")
                            time.sleep(retry_delay)
                        else:
                            print(f"[ERROR] API 요청 실패 (최대 재시도 초과): {e}")
                            return all_data
                    else:
                        print(f"[ERROR] API 요청 오류: {e}")
                        return all_data
                except Exception as e:
                    print(f"[ERROR] API 요청 오류: {e}")
                    return all_data

            if not success or not next_url:
                break

        return all_data

    def fetch_ad_creatives(self, ad_account_id: str) -> Dict[str, Dict]:
        """광고 크리에이티브 정보 가져오기"""
        fields = [
            'id', 'name', 'preview_shareable_link',
            'creative{id,title,body,call_to_action_type,image_url,thumbnail_url,video_id,link_url,object_story_spec,asset_feed_spec}'
        ]

        url = f"{self.base_url}/{ad_account_id}/ads"
        params = {
            'access_token': self.access_token,
            'fields': ','.join(fields),
            'limit': 100
        }

        ad_creatives_map = {}
        image_hashes_to_fetch = {}  # ad_id -> hash 매핑

        try:
            while url:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                for ad in data.get('data', []):
                    ad_id = ad.get('id')
                    creative = ad.get('creative', {})
                    preview_url = ad.get('preview_shareable_link', '')  # 광고 미리보기 URL

                    # 기본 필드에서 추출
                    link_url = creative.get('link_url', '')
                    image_url = creative.get('image_url', '')
                    thumbnail_url = creative.get('thumbnail_url', '')

                    # object_story_spec에서 link_url, image_url 추출
                    oss = creative.get('object_story_spec', {})
                    link_data = oss.get('link_data', {})
                    video_data = oss.get('video_data', {})
                    template_data = oss.get('template_data', {})  # Catalog Ads

                    if not link_url:
                        link_url = link_data.get('link', '') or video_data.get('link', '')

                    # template_data에서 링크 추출 (Catalog Ads)
                    if not link_url and template_data:
                        link_url = template_data.get('link', '')

                    if not image_url:
                        image_url = link_data.get('picture', '') or video_data.get('image_url', '')

                    # asset_feed_spec에서 추출 (Dynamic Creative)
                    first_image_hash = ''
                    asset_feed = creative.get('asset_feed_spec', {})

                    # link_urls에서 링크 추출 (Dynamic Creative)
                    if not link_url and asset_feed:
                        link_urls = asset_feed.get('link_urls', [])
                        if link_urls:
                            # website_url 또는 display_url 사용
                            first_link = link_urls[0] if isinstance(link_urls[0], dict) else {}
                            link_url = first_link.get('website_url', '') or first_link.get('display_url', '')
                            # 문자열인 경우 직접 사용
                            if not link_url and isinstance(link_urls[0], str):
                                link_url = link_urls[0]

                    if asset_feed and 'images' in asset_feed:
                        images = asset_feed.get('images', [])
                        if images:
                            first_image_hash = images[0].get('hash', '')
                            if first_image_hash and not image_url:
                                image_hashes_to_fetch[ad_id] = first_image_hash

                    ad_creatives_map[ad_id] = {
                        'creative_id': creative.get('id', ''),
                        'title': creative.get('title', ''),
                        'body': creative.get('body', ''),
                        'cta': creative.get('call_to_action_type', ''),
                        'link_url': link_url,
                        'image_url': image_url,
                        'video_id': creative.get('video_id', ''),
                        'thumbnail_url': thumbnail_url,
                        'preview_url': preview_url,  # 광고 미리보기 URL
                        '_image_hash': first_image_hash  # 임시 저장
                    }

                url = data.get('paging', {}).get('next')
                params = {}

        except Exception as e:
            print(f"[WARNING] 크리에이티브 조회 오류: {e}")

        # Fallback 및 정리 (에러 발생 여부와 관계없이 항상 실행)
        # 이미지 해시로 실제 URL 조회
        if image_hashes_to_fetch and ad_creatives_map:
            try:
                unique_hashes = list(set(image_hashes_to_fetch.values()))
                hash_to_url = self._fetch_image_urls_by_hash(ad_account_id, unique_hashes)

                for ad_id, img_hash in image_hashes_to_fetch.items():
                    if ad_id in ad_creatives_map and img_hash in hash_to_url:
                        ad_creatives_map[ad_id]['image_url'] = hash_to_url[img_hash]
            except Exception as e:
                print(f"[WARNING] 이미지 해시 URL 조회 오류: {e}")

        # Fallback: image_url이 여전히 없으면 thumbnail_url 사용
        for ad_id, creative_data in ad_creatives_map.items():
            if not creative_data.get('image_url') and creative_data.get('thumbnail_url'):
                creative_data['image_url'] = creative_data['thumbnail_url']
            # 임시 필드 제거
            creative_data.pop('_image_hash', None)

        return ad_creatives_map

    def _fetch_image_urls_by_hash(self, ad_account_id: str, hashes: List[str]) -> Dict[str, str]:
        """이미지 해시로 실제 이미지 URL 조회"""
        import json

        hash_to_url = {}
        if not hashes:
            return hash_to_url

        url = f"{self.base_url}/{ad_account_id}/adimages"
        params = {
            'access_token': self.access_token,
            'fields': 'hash,url',
            'hashes': json.dumps(hashes)
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            for img in data.get('data', []):
                img_hash = img.get('hash')
                img_url = img.get('url')
                if img_hash and img_url:
                    hash_to_url[img_hash] = img_url

        except Exception as e:
            print(f"[WARNING] 이미지 URL 조회 오류: {e}")

        return hash_to_url
