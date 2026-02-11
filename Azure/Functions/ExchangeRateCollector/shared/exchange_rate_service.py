"""
환율 수집 서비스
- 한국은행 Open API로 USD/KRW 환율 조회
- SystemConfig 테이블 업데이트 + 이력 기록
"""

import logging
from datetime import datetime, timedelta
import requests
from database import get_db_connection

logger = logging.getLogger(__name__)

# 한국은행 API 설정
BOK_API_BASE_URL = "https://ecos.bok.or.kr/api/StatisticSearch"
STAT_CODE = "731Y001"       # 평균환율/기간별
ITEM_CODE = "0000001"       # 원/미달러
CYCLE = "D"                 # 일별


def get_api_key(conn) -> str:
    """SystemConfig에서 BOK_API_KEY 조회"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ConfigValue FROM SystemConfig "
        "WHERE Category = 'Common' AND ConfigKey = 'BOK_API_KEY' AND IsActive = 1"
    )
    row = cursor.fetchone()
    cursor.close()

    if not row:
        raise ValueError("SystemConfig에 BOK_API_KEY가 등록되어 있지 않습니다.")
    return row[0]


def fetch_exchange_rate(api_key: str, target_date: str) -> dict | None:
    """
    한국은행 API에서 당일 USD/KRW 환율 조회

    Args:
        api_key: 한국은행 Open API 인증키
        target_date: 조회일자 (YYYYMMDD)

    Returns:
        환율 데이터 dict 또는 None (데이터 없음)
    """
    url = f"{BOK_API_BASE_URL}/{api_key}/JSON/kr/1/10/{STAT_CODE}/{CYCLE}/{target_date}/{target_date}/{ITEM_CODE}"

    logger.info(f"[API] 한국은행 환율 조회: {target_date}")

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    # API 에러 체크
    if "RESULT" in data:
        result_code = data["RESULT"]["CODE"]
        if result_code == "INFO-200":
            # 해당 날짜 데이터 없음 (주말/공휴일)
            logger.info(f"[API] {target_date}: 데이터 없음 (주말/공휴일)")
            return None
        else:
            raise ValueError(f"한국은행 API 오류: {data['RESULT']['CODE']} - {data['RESULT']['MESSAGE']}")

    # 정상 응답 파싱
    stat_search = data.get("StatisticSearch", {})
    rows = stat_search.get("row", [])

    if not rows:
        logger.info(f"[API] {target_date}: 데이터 없음")
        return None

    row = rows[-1]  # 가장 최신 데이터
    rate_value = row.get("DATA_VALUE", "").replace(",", "")

    if not rate_value:
        logger.warning(f"[API] {target_date}: DATA_VALUE 비어있음")
        return None

    return {
        "rate": int(float(rate_value)),
        "rate_raw": rate_value,
        "date": row.get("TIME", target_date),
        "stat_name": row.get("STAT_NAME", ""),
        "item_name": row.get("ITEM_NAME1", ""),
    }


def update_exchange_rate(conn, new_rate: int) -> bool:
    """
    SystemConfig의 USD_TO_KRW_RATE 업데이트 + 이력 기록

    Args:
        conn: DB 연결
        new_rate: 새로운 환율값 (정수)

    Returns:
        True: 업데이트 됨, False: 변경 없음 (동일 값)
    """
    cursor = conn.cursor()

    try:
        # 현재 값 조회
        cursor.execute(
            "SELECT ConfigID, ConfigValue FROM SystemConfig "
            "WHERE Category = 'Common' AND ConfigKey = 'USD_TO_KRW_RATE' AND IsActive = 1"
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError("SystemConfig에 USD_TO_KRW_RATE가 등록되어 있지 않습니다.")

        config_id = row[0]
        old_value = row[1]
        new_value = str(new_rate)

        # 동일 값이면 skip
        if old_value == new_value:
            logger.info(f"[DB] 환율 변경 없음: {old_value}")
            return False

        # SystemConfig 업데이트
        cursor.execute(
            "UPDATE SystemConfig SET ConfigValue = ?, UpdatedDate = GETDATE(), UpdatedBy = ? "
            "WHERE ConfigID = ?",
            new_value, "AzureFunction_ExchangeRate", config_id
        )

        # SystemConfigHistory에 이력 기록
        cursor.execute(
            "INSERT INTO SystemConfigHistory "
            "(ConfigID, Category, ConfigKey, OldValue, NewValue, ChangedBy, ChangedDate, ChangeReason) "
            "VALUES (?, 'Common', 'USD_TO_KRW_RATE', ?, ?, ?, GETDATE(), ?)",
            config_id, old_value, new_value,
            "AzureFunction_ExchangeRate",
            f"한국은행 매매기준율 자동 업데이트: {old_value} → {new_value}"
        )

        conn.commit()
        logger.info(f"[DB] 환율 업데이트 완료: {old_value} → {new_value}")
        return True

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def collect_exchange_rate() -> dict:
    """
    환율 수집 메인 로직
    1. DB에서 API 키 조회
    2. 한국은행 API로 당일 환율 조회
    3. 데이터 있으면 SystemConfig 업데이트

    Returns:
        실행 결과 dict
    """
    today = datetime.utcnow() + timedelta(hours=9)  # KST
    target_date = today.strftime("%Y%m%d")

    logger.info(f"환율 수집 시작: {target_date} (KST)")

    conn = get_db_connection()

    try:
        # 1. API 키 조회
        api_key = get_api_key(conn)

        # 2. 당일 환율 조회
        rate_data = fetch_exchange_rate(api_key, target_date)

        if rate_data is None:
            return {
                "status": "skipped",
                "date": target_date,
                "reason": "주말/공휴일 - 데이터 없음"
            }

        # 3. SystemConfig 업데이트
        updated = update_exchange_rate(conn, rate_data["rate"])

        return {
            "status": "updated" if updated else "unchanged",
            "date": target_date,
            "rate": rate_data["rate"],
            "rate_raw": rate_data["rate_raw"],
        }

    finally:
        conn.close()
