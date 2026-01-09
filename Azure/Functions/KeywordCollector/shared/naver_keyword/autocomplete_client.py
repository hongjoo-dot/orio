"""
네이버 자동완성 API 클라이언트
복합키워드 수집 기능
"""
import requests
import logging


class NaverAutocompleteClient:
    """네이버 자동완성 API 클라이언트"""

    def __init__(self):
        self.base_url = "https://ac.search.naver.com/nx/ac"

    def get_autocomplete_keywords(self, keyword, max_results=10):
        """
        네이버 자동완성 API를 통해 복합키워드 수집

        Args:
            keyword: 조회할 키워드
            max_results: 최대 결과 개수 (기본값: 10)

        Returns:
            list: 자동완성 키워드 리스트 또는 빈 리스트
        """
        params = {
            "q": keyword,
            "con": "1",
            "frm": "nx",
            "ans": "2",
            "r_format": "json",
            "r_enc": "UTF-8",
            "r_unicode": "0",
            "t_koreng": "1",
            "run": "2",
            "rev": "4",
            "q_enc": "UTF-8",
            "st": "100"
        }

        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()

            # 응답 구조: {"items": [[[keyword, score], ...], ...]}
            # items[0]이 첫 번째 그룹, 각 항목은 [keyword, score] 형태
            autocomplete_list = []

            if "items" in result and isinstance(result["items"], list) and len(result["items"]) > 0:
                first_group = result["items"][0]
                if isinstance(first_group, list):
                    for item in first_group:
                        if isinstance(item, list) and len(item) > 0:
                            autocomplete_keyword = item[0]
                            autocomplete_list.append(autocomplete_keyword)

            # 상위 N개만 반환
            autocomplete_list = autocomplete_list[:max_results]

            logging.info(f"자동완성 '{keyword}': {len(autocomplete_list)}개 수집 (상위 {max_results}개)")

            return autocomplete_list

        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP 에러 (자동완성: {keyword}): {e}")
            return []
        except requests.exceptions.RequestException as e:
            logging.error(f"네트워크 에러 (자동완성: {keyword}): {e}")
            return []
        except Exception as e:
            logging.error(f"자동완성 API 호출 에러 (키워드: {keyword}): {e}")
            return []
