"""
Cafe24 고객 데이터 수집 모듈
Dynamic Cursor 방식으로 전체 고객 수집 (offset 8000 제한 우회)
"""
import requests
import time
import logging
from datetime import datetime, timedelta
from .collector import Cafe24OrderCollector


class Cafe24CustomerCollector(Cafe24OrderCollector):
    """Cafe24 고객 데이터 수집기 (토큰 관리 상속)"""

    def _generate_monthly_ranges(self, start_date, end_date):
        """
        시작일부터 종료일까지 1개월 단위로 날짜 범위 생성
        """
        ranges = []
        current_start = start_date

        while current_start < end_date:
            # 1개월(30일) 단위로 변경
            current_end = current_start + timedelta(days=30)
            if current_end > end_date:
                current_end = end_date

            ranges.append((current_start, current_end))
            current_start = current_end

        return ranges

    def _collect_range_with_filtering(self, range_start_date, range_end_date):
        """
        특정 날짜 범위의 고객 데이터 수집 (date_type=join 사용)
        """
        access_token = self.get_access_token()
        url = f"{self.base_url}/admin/customersprivacy"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Cafe24-Api-Version": "2025-12-01"
        }

        range_customers = []
        offset = 0
        limit = 1000
        
        start_str = range_start_date.strftime('%Y-%m-%d')
        end_str = range_end_date.strftime('%Y-%m-%d')

        logging.info(f"  범위 수집: {start_str} ~ {end_str}")

        while True:
            # search_type='created_date' 대신 기본 검색(customer_info) + date_type='join' 사용
            # 이를 통해 start_date, end_date 범위를 지정 가능
            params = {
                "limit": limit,
                "offset": offset,
                "date_type": "join",      # 가입일 기준
                "start_date": start_str,  # 시작일
                "end_date": end_str       # 종료일
            }

            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)

                if response.status_code == 401:
                    logging.warning("토큰 만료, 자동 갱신 중...")
                    access_token = self.get_access_token()
                    headers["Authorization"] = f"Bearer {access_token}"
                    continue

                if response.status_code == 429:
                    logging.warning("API 호출 제한, 2초 대기...")
                    time.sleep(2)
                    continue

                if response.status_code == 422:
                    logging.warning(f"offset {offset} 한도 도달 (422). 이 범위의 데이터가 8000건을 초과했을 수 있음.")
                    break

                if response.status_code != 200:
                    logging.error(f"조회 실패: {response.status_code}, {response.text}")
                    break

                data = response.json()
                customers = data.get("customersprivacy", [])

                if not customers:
                    break

                # 데이터 추가
                range_customers.extend(customers)
                logging.info(f"  offset {offset}: {len(customers)}명 수신 (누적: {len(range_customers)}명)")

                offset += limit
                time.sleep(0.5)

            except Exception as e:
                logging.error(f"수집 중 오류: {e}", exc_info=True)
                break

        return range_customers

    def collect_all_customers(self):
        """
        전체 고객 데이터 수집 (날짜 범위 분할 방식)
        """
        logging.info("=" * 70)
        logging.info("Cafe24 전체 고객 데이터 수집 시작 (Date Range Chunking)")
        logging.info("=" * 70)

        # 시작일 설정 (2024-06-01)
        start_date = datetime(2024, 6, 1)
        end_date = datetime.now() + timedelta(days=1)

        logging.info(f"수집 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

        # 날짜 범위 생성
        date_ranges = self._generate_monthly_ranges(start_date, end_date)
        logging.info(f"총 {len(date_ranges)}개 범위로 분할")

        all_customers = []
        seen_member_ids = set()

        for idx, (range_start, range_end) in enumerate(date_ranges, 1):
            logging.info(f"[범위 {idx}/{len(date_ranges)}]")
            customers = self._collect_range_with_filtering(range_start, range_end)

            # 중복 제거
            unique_customers = []
            for customer in customers:
                member_id = customer.get('member_id')
                if member_id and member_id not in seen_member_ids:
                    seen_member_ids.add(member_id)
                    unique_customers.append(customer)

            logging.info(f"  중복 제거: {len(customers)}명 → {len(unique_customers)}명 (중복 {len(customers) - len(unique_customers)}명)")
            all_customers.extend(unique_customers)

        logging.info("=" * 70)
        logging.info(f"수집 완료: 총 {len(all_customers)}명 (고유)")
        logging.info("=" * 70)

        return all_customers


if __name__ == "__main__":
    """테스트 실행"""
    import json

    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("Cafe24 고객 데이터 수집 테스트")
    print("=" * 70)

    collector = Cafe24CustomerCollector()
    customers = collector.collect_all_customers()

    if customers:
        print(f"\n[결과] {len(customers)}명의 고객 데이터 수집 완료")
        print("\n[샘플 데이터] 첫 번째 고객:")
        print(json.dumps(customers[0], indent=2, ensure_ascii=False))
    else:
        print("\n[결과] 수집된 고객 데이터 없음")
