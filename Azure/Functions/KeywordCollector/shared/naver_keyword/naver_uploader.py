"""
네이버 키워드 검색량 데이터 DB 업로드 (새 스키마)
"""
import logging
from datetime import datetime
from common.database import get_db_connection


class NaverAdsUploader:
    """네이버 검색광고 데이터 업로더"""

    def upload_search_volume(self, keyword_id, brand_id, base_keyword, compound_keyword, keyword_list, collection_date, hint_only=False):
        """
        네이버 검색광고 검색량 데이터를 NaverAdsSearchVolume 테이블에 업로드

        Args:
            keyword_id: 키워드 ID (FK)
            brand_id: 브랜드 ID (FK)
            base_keyword: Keyword 테이블의 기본 키워드 (예: "스크럽대디")
            compound_keyword: 자동완성에서 수집된 복합키워드 (공백 포함, 예: "스크럽대디 수세미")
            keyword_list: API 응답의 keywordList (공백 제거된 키워드로 조회한 결과)
            collection_date: 수집 날짜 (YYYY-MM-DD)
            hint_only: True이면 힌트 키워드만 저장 (연관 키워드 제외)

        Returns:
            int: 삽입된 레코드 수
        """
        if not keyword_list:
            logging.warning("업로드할 키워드 데이터가 없습니다")
            return 0

        conn = None
        inserted_count = 0

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            for item in keyword_list:
                # API 응답의 relKeyword (공백 제거된 버전)
                api_rel_keyword = item.get('relKeyword', '')

                # 숫자 필드 안전하게 변환
                pc_cnt = self._parse_search_count(item.get('monthlyPcQcCnt', 0))
                mobile_cnt = self._parse_search_count(item.get('monthlyMobileQcCnt', 0))
                total_cnt = pc_cnt + mobile_cnt

                # API 응답의 relKeyword(공백제거)와 compound_keyword(공백제거)를 비교
                # 일치하면 해당 데이터를 compound_keyword(공백포함)로 저장
                api_normalized = api_rel_keyword.replace(' ', '').lower()
                compound_normalized = compound_keyword.replace(' ', '').lower()

                # API 응답이 요청한 키워드와 일치하는 경우만 저장
                if api_normalized != compound_normalized:
                    continue

                # IsMainKeyword 판별 (공백 제거 후 비교, 대소문자 무시)
                # 1 = 기본 키워드 (Keyword 테이블의 키워드)
                # 0 = 복합 키워드 (자동완성으로 수집된 키워드)
                base_normalized = base_keyword.replace(' ', '').lower()
                is_main_keyword = 1 if compound_normalized == base_normalized else 0

                # 월간 총 검색량 30 미만 필터링 (Main 키워드는 제외)
                if total_cnt < 30 and not is_main_keyword:
                    continue

                pc_click = float(item.get('monthlyAvePcClkCnt', 0)) if item.get('monthlyAvePcClkCnt') else 0
                mobile_click = float(item.get('monthlyAveMobileClkCnt', 0)) if item.get('monthlyAveMobileClkCnt') else 0
                pc_ctr = float(item.get('monthlyAvePcCtr', 0)) if item.get('monthlyAvePcCtr') else 0
                mobile_ctr = float(item.get('monthlyAveMobileCtr', 0)) if item.get('monthlyAveMobileCtr') else 0

                comp_idx = item.get('compIdx', '')
                avg_depth = float(item.get('plAvgDepth', 0)) if item.get('plAvgDepth') else 0

                # MERGE 쿼리 (UPSERT)
                # Keyword = Keyword 테이블의 기본 키워드 (예: "스크럽대디")
                # CompoundKeyword = 자동완성/검색된 복합키워드 (예: "스크럽대디 스티커")
                # IsMainKeyword = 1 (기본), 0 (복합)
                merge_query = """
                MERGE INTO NaverAdsSearchVolume AS target
                USING (SELECT ? AS KeywordID, ? AS CompoundKeyword, ? AS CollectionDate) AS source
                ON (target.KeywordID = source.KeywordID AND target.CompoundKeyword = source.CompoundKeyword AND target.CollectionDate = source.CollectionDate)
                WHEN MATCHED THEN
                    UPDATE SET
                        BrandID = ?,
                        Keyword = ?,
                        MonthlyPcSearchCount = ?,
                        MonthlyMobileSearchCount = ?,
                        MonthlyTotalSearchCount = ?,
                        MonthlyAvgPcClickCount = ?,
                        MonthlyAvgMobileClickCount = ?,
                        MonthlyAvgPcCtr = ?,
                        MonthlyAvgMobileCtr = ?,
                        CompetitionIndex = ?,
                        AvgAdDepth = ?,
                        IsMainKeyword = ?
                WHEN NOT MATCHED THEN
                    INSERT (
                        KeywordID,
                        BrandID,
                        Keyword,
                        CompoundKeyword,
                        MonthlyPcSearchCount,
                        MonthlyMobileSearchCount,
                        MonthlyTotalSearchCount,
                        MonthlyAvgPcClickCount,
                        MonthlyAvgMobileClickCount,
                        MonthlyAvgPcCtr,
                        MonthlyAvgMobileCtr,
                        CompetitionIndex,
                        AvgAdDepth,
                        CollectionDate,
                        IsMainKeyword
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """

                cursor.execute(merge_query, (
                    keyword_id, compound_keyword, collection_date,  # USING clause
                    brand_id, base_keyword, pc_cnt, mobile_cnt, total_cnt,
                    pc_click, mobile_click, pc_ctr, mobile_ctr, comp_idx, avg_depth, is_main_keyword,  # UPDATE SET
                    keyword_id, brand_id, base_keyword, compound_keyword, pc_cnt, mobile_cnt, total_cnt,
                    pc_click, mobile_click, pc_ctr, mobile_ctr, comp_idx, avg_depth, collection_date, is_main_keyword  # INSERT VALUES
                ))

                inserted_count += 1

            conn.commit()
            logging.info(f"DB 업로드 완료: {inserted_count}개 레코드 (KeywordID: {keyword_id})")

        except Exception as e:
            if conn:
                conn.rollback()
            logging.error(f"DB 업로드 실패 (KeywordID: {keyword_id}): {e}")
            raise

        finally:
            if conn:
                cursor.close()
                conn.close()

        return inserted_count

    def _parse_search_count(self, value):
        """
        검색량 값을 정수로 변환 ("< 10" 같은 문자열 처리)

        Args:
            value: 검색량 값

        Returns:
            int: 변환된 정수
        """
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            # "< 10" 같은 경우 0으로 처리
            if '<' in value:
                return 0
            # 숫자 문자열인 경우
            clean_value = value.replace(',', '').strip()
            if clean_value.isdigit():
                return int(clean_value)
        return 0
