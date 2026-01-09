import logging
import json
from common.database import get_db_connection

class GoogleAdsUploader:
    def __init__(self):
        pass

    def upload_metrics(self, keyword_id, brand_id, keyword_text, metrics, collection_date):
        """
        구글 키워드 지표를 DB에 업로드 (UPSERT)
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 월별 히스토리 JSON 변환
            monthly_searches = []
            for month in metrics.monthly_search_volumes:
                monthly_searches.append({
                    'year': month.year,
                    'month': month.month.name,
                    'count': month.monthly_searches
                })
            
            history_json = json.dumps(monthly_searches, ensure_ascii=False)

            # MERGE 쿼리
            merge_query = """
            MERGE INTO GoogleAdsSearchVolume AS target
            USING (SELECT ? AS KeywordID, ? AS CollectionDate) AS source
            ON (target.KeywordID = source.KeywordID AND target.CollectionDate = source.CollectionDate)
            WHEN MATCHED THEN
                UPDATE SET
                    BrandID = ?,
                    Keyword = ?,
                    AvgMonthlySearches = ?,
                    Competition = ?,
                    CompetitionIndex = ?,
                    LowTopOfPageBid = ?,
                    HighTopOfPageBid = ?,
                    MonthlyHistory = ?
            WHEN NOT MATCHED THEN
                INSERT (KeywordID, BrandID, Keyword, AvgMonthlySearches, Competition, CompetitionIndex, LowTopOfPageBid, HighTopOfPageBid, MonthlyHistory, CollectionDate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """

            low_bid = metrics.low_top_of_page_bid_micros / 1000000 if metrics.low_top_of_page_bid_micros else 0
            high_bid = metrics.high_top_of_page_bid_micros / 1000000 if metrics.high_top_of_page_bid_micros else 0

            cursor.execute(merge_query, (
                keyword_id, collection_date,  # USING
                brand_id, keyword_text, metrics.avg_monthly_searches, metrics.competition.name, metrics.competition_index, low_bid, high_bid, history_json,  # UPDATE
                keyword_id, brand_id, keyword_text, metrics.avg_monthly_searches, metrics.competition.name, metrics.competition_index, low_bid, high_bid, history_json, collection_date # INSERT
            ))
            
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Google Ads DB 업로드 실패 ({keyword_text}): {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
