"""
네이버 검색광고 ID → 이름 매핑 모듈
캠페인/광고그룹/키워드/소재 ID를 이름으로 변환
"""

import requests
from .auth import NaverAuth

BASE_URL = "https://api.naver.com"


class NaverNameMapper:
    """ID를 이름으로 매핑하는 클래스"""

    def __init__(self):
        self.auth = NaverAuth()
        self.base_url = BASE_URL

        # 캐시
        self.campaign_cache = {}
        self.campaign_status_cache = {}  # 캠페인 상태 캐시 (ENABLED, PAUSED 등)
        self.adgroup_cache = {}
        self.keyword_cache = {}
        self.ad_cache = {}

    def build_all_mappings(self):
        """모든 매핑 테이블 구축"""
        print("\n[매핑 테이블 구축]")

        # 1. 캠페인 조회
        campaigns = self._get_campaigns()
        print(f"   캠페인: {len(campaigns)}개")

        for campaign in campaigns:
            campaign_id = campaign.get('nccCampaignId')
            campaign_name = campaign.get('name')
            campaign_status = campaign.get('status', 'UNKNOWN')  # ELIGIBLE, PAUSED 등
            user_lock = campaign.get('userLock', True)  # True=OFF, False=ON

            self.campaign_cache[campaign_id] = campaign_name
            # 활성 조건: status가 ELIGIBLE이고 userLock이 False(ON)
            is_active = (campaign_status == 'ELIGIBLE' and user_lock == False)
            self.campaign_status_cache[campaign_id] = 'ACTIVE' if is_active else 'INACTIVE'

            # 2. 광고그룹 조회
            adgroups = self._get_adgroups(campaign_id)

            for adgroup in adgroups:
                adgroup_id = adgroup.get('nccAdgroupId')
                adgroup_name = adgroup.get('name')
                self.adgroup_cache[adgroup_id] = adgroup_name

                # 3. 키워드 조회
                keywords = self._get_keywords(adgroup_id)
                for keyword in keywords:
                    keyword_id = keyword.get('nccKeywordId')
                    keyword_text = keyword.get('keyword', '')
                    self.keyword_cache[keyword_id] = keyword_text

                # 4. 소재 조회
                ads = self._get_ads(adgroup_id)
                for ad in ads:
                    ad_id = ad.get('nccAdId')
                    ad_name = ad.get('name', '')
                    self.ad_cache[ad_id] = ad_name

        # 캠페인 상태별 카운트
        active_count = sum(1 for s in self.campaign_status_cache.values() if s == 'ACTIVE')
        inactive_count = sum(1 for s in self.campaign_status_cache.values() if s == 'INACTIVE')
        print(f"   캠페인 상태: 활성(ON+노출가능) {active_count}개, 비활성 {inactive_count}개")
        print(f"   광고그룹: {len(self.adgroup_cache)}개")
        print(f"   키워드: {len(self.keyword_cache)}개")
        print(f"   소재: {len(self.ad_cache)}개")
        print(f"   [OK] 매핑 완료")

        return {
            'campaign': self.campaign_cache,
            'adgroup': self.adgroup_cache,
            'keyword': self.keyword_cache,
            'ad': self.ad_cache
        }

    def get_name(self, entity_type: str, entity_id: str) -> str:
        """ID로 이름 조회"""
        cache_map = {
            'campaign': self.campaign_cache,
            'adgroup': self.adgroup_cache,
            'keyword': self.keyword_cache,
            'ad': self.ad_cache
        }

        cache = cache_map.get(entity_type, {})
        return cache.get(entity_id, entity_id)

    def get_campaign_status(self, campaign_id: str) -> str:
        """캠페인 ID로 상태 조회 (ENABLED, PAUSED, DELETED 등)"""
        return self.campaign_status_cache.get(campaign_id, 'UNKNOWN')

    def is_campaign_enabled(self, campaign_id: str) -> bool:
        """캠페인이 활성 상태인지 확인 (ON + 노출가능)"""
        return self.get_campaign_status(campaign_id) == 'ACTIVE'

    def _get_campaigns(self) -> list:
        """캠페인 목록 조회"""
        uri = '/ncc/campaigns'
        headers = self.auth.get_headers('GET', uri)

        try:
            response = requests.get(f"{self.base_url}{uri}", headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []

    def _get_adgroups(self, campaign_id: str) -> list:
        """광고그룹 목록 조회"""
        uri = '/ncc/adgroups'
        headers = self.auth.get_headers('GET', uri)

        try:
            response = requests.get(
                f"{self.base_url}{uri}",
                headers=headers,
                params={'nccCampaignId': campaign_id},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []

    def _get_keywords(self, adgroup_id: str) -> list:
        """키워드 목록 조회"""
        uri = '/ncc/keywords'
        headers = self.auth.get_headers('GET', uri)

        try:
            response = requests.get(
                f"{self.base_url}{uri}",
                headers=headers,
                params={'nccAdgroupId': adgroup_id},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []

    def _get_ads(self, adgroup_id: str) -> list:
        """소재 목록 조회"""
        uri = '/ncc/ads'
        headers = self.auth.get_headers('GET', uri)

        try:
            response = requests.get(
                f"{self.base_url}{uri}",
                headers=headers,
                params={'nccAdgroupId': adgroup_id},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []
