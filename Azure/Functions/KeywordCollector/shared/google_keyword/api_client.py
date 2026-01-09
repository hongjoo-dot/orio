import os
import logging
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from common.system_config import get_config

class GoogleAdsKeywordClient:
    def __init__(self):
        try:
            config = get_config()
            
            # SystemConfig에서 설정 가져오기
            google_config = {
                "developer_token": config.get("GoogleKeywordAPI", "developer_token"),
                "client_id": config.get("GoogleKeywordAPI", "client_id"),
                "client_secret": config.get("GoogleKeywordAPI", "client_secret"),
                "refresh_token": config.get("GoogleKeywordAPI", "refresh_token"),
                "login_customer_id": config.get("GoogleKeywordAPI", "manager_customer_id"),
                "use_proto_plus": True
            }
            
            # 필수 설정 체크
            if not all([google_config["developer_token"], google_config["client_id"], google_config["refresh_token"]]):
                raise ValueError("Google Ads API 필수 설정이 SystemConfig에 누락되었습니다.")

            self.client = GoogleAdsClient.load_from_dict(google_config)
        except Exception as e:
            logging.error(f"Google Ads 설정 로드 실패 (SystemConfig): {e}")
            raise

    def get_historical_metrics(self, customer_id, keywords):
        """
        키워드 리스트에 대한 과거 검색 지표 조회
        """
        if not keywords:
            return []

        keyword_plan_idea_service = self.client.get_service("KeywordPlanIdeaService")
        
        request = self.client.get_type("GenerateKeywordHistoricalMetricsRequest")
        request.customer_id = customer_id
        request.keywords.extend(keywords)
        
        # 언어: 한국어 (1019)
        request.language = "languageConstants/1019"
        # 지역: 대한민국 (2410)
        request.geo_target_constants.append("geoTargetConstants/2410")
        
        try:
            response = keyword_plan_idea_service.generate_keyword_historical_metrics(
                request=request
            )
            return response.results
        except GoogleAdsException as ex:
            logging.error(f"Google Ads API 요청 실패: {ex.error.code().name}")
            for error in ex.failure.errors:
                logging.error(f"\tError: {error.message}")
            return None
