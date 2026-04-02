"""
사방넷 풀필먼트 REST API 클라이언트
- HMAC-SHA256 인증
- 재고조회, 로케이션 재고, 입고예정, 입고작업내역 API
- 페이지네이션 자동 처리
"""

import hmac
import hashlib
import base64
import requests
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class SabangnetFulfillmentClient:
    """사방넷 풀필먼트 API 클라이언트"""

    def __init__(self, config: dict):
        self.api_host = config['api_host']
        self.access_key = config['api_access_key']
        self.secret_key = config['api_secret_key']
        self.company_code = config['company_code']
        self.member_id = config['member_id']

        self._signature_cache = {}

    # ============================================================
    # 인증
    # ============================================================
    def _generate_signature(self) -> str:
        """HMAC-SHA256 Signature 생성 (일별 캐싱)"""
        date_str = datetime.today().strftime("%Y%m%d")

        if date_str in self._signature_cache:
            return self._signature_cache[date_str]

        date_key = hmac.new(
            bytes(self.secret_key, 'utf-8'),
            bytes(date_str, 'utf-8'),
            hashlib.sha256
        ).hexdigest()

        sign_key = hmac.new(
            bytes(date_key, 'utf-8'),
            bytes(self.access_key, 'utf-8'),
            hashlib.sha256
        ).hexdigest()

        signature = base64.b64encode(sign_key.encode('utf-8')).decode('utf-8')

        self._signature_cache = {date_str: signature}
        return signature

    def _get_headers(self) -> dict:
        """인증 헤더 생성"""
        date_str = datetime.today().strftime("%Y%m%d")
        return {
            'Authorization': 'LIVE-HMAC-SHA256',
            'Credential': f'{self.company_code}/{self.access_key}/{date_str}/srwms_request',
            'Signature': self._generate_signature()
        }

    def _request(self, method: str, path: str, params: dict = None, max_retries: int = 3) -> dict:
        """API 요청 (재시도 로직 포함)"""
        url = f"{self.api_host}{path}"
        headers = self._get_headers()

        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.request(method, url, headers=headers, params=params, timeout=30)

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('code') == '9999':
                        return data
                    else:
                        logger.warning(f"[API] 응답 에러: code={data.get('code')}, message={data.get('message')}")
                        return data

                elif resp.status_code == 429:
                    wait = min(5 * attempt, 30)
                    logger.warning(f"[API] Rate limit, {wait}초 대기 (시도 {attempt}/{max_retries})")
                    time.sleep(wait)
                    continue

                elif resp.status_code >= 500:
                    logger.warning(f"[API] 서버 오류 {resp.status_code} (시도 {attempt}/{max_retries})")
                    if attempt < max_retries:
                        time.sleep(3 * attempt)
                        continue
                    return {'code': str(resp.status_code), 'message': resp.text}

                else:
                    logger.warning(f"[API] HTTP {resp.status_code}: {resp.text[:200]}")
                    return {'code': str(resp.status_code), 'message': resp.text}

            except requests.Timeout:
                logger.warning(f"[API] 타임아웃 (시도 {attempt}/{max_retries})")
                if attempt < max_retries:
                    time.sleep(3)
            except requests.RequestException as e:
                logger.error(f"[API] 요청 실패: {e}")
                if attempt < max_retries:
                    time.sleep(3)

        return {'code': 'TIMEOUT', 'message': '모든 재시도 실패'}

    # ============================================================
    # 재고 API
    # ============================================================
    def get_stocks(self, shipping_product_ids: list) -> list:
        """
        재고조회 (벌크) - 100개씩 배치 처리, 전체 페이지 수집

        Args:
            shipping_product_ids: 출고상품 ID 리스트

        Returns:
            list: 재고 데이터 리스트
        """
        all_stocks = []

        # 100개씩 배치
        for i in range(0, len(shipping_product_ids), 100):
            batch_ids = shipping_product_ids[i:i + 100]
            logger.info(f"[재고조회] 배치 {i // 100 + 1}: {len(batch_ids)}개 상품")

            page = 1
            while True:
                params = {'member_id': self.member_id, 'page': page}
                for idx, pid in enumerate(batch_ids):
                    params[f'shipping_product_ids[{idx}]'] = pid

                resp = self._request('GET', '/v2/inventory/stocks', params)

                if resp.get('code') != '9999':
                    logger.warning(f"[재고조회] 실패: {resp.get('message')}")
                    break

                response = resp.get('response', {})
                data_list = response.get('data_list', [])
                all_stocks.extend(data_list)

                total_page = int(response.get('total_page', 1))
                if page >= total_page:
                    break
                page += 1

            # API 호출 간격
            if i + 100 < len(shipping_product_ids):
                time.sleep(0.5)

        logger.info(f"[재고조회] 완료: {len(all_stocks)}건")
        return all_stocks

    def get_stock_locations(self, shipping_product_ids: list, loc_type: int = None) -> list:
        """
        로케이션 재고조회 (다중상품)

        Args:
            shipping_product_ids: 출고상품 ID 리스트
            loc_type: 재고 구분 (2=출고가능 등). None이면 전체

        Returns:
            list: 로케이션별 재고 리스트
        """
        all_locations = []

        for i in range(0, len(shipping_product_ids), 100):
            batch_ids = shipping_product_ids[i:i + 100]

            params = {}
            for idx, pid in enumerate(batch_ids):
                params[f'shipping_product_ids[{idx}]'] = pid
            if loc_type is not None:
                params['loc_type'] = loc_type

            resp = self._request('GET', '/v2/inventory/stock/locations', params)

            if resp.get('code') != '9999':
                logger.warning(f"[로케이션조회] 실패: {resp.get('message')}")
                continue

            response = resp.get('response', {})
            data_list = response.get('data_list', [])
            all_locations.extend(data_list)

            if i + 100 < len(shipping_product_ids):
                time.sleep(0.5)

        logger.info(f"[로케이션조회] 완료: {len(all_locations)}건")
        return all_locations

    # ============================================================
    # 출고상품 API
    # ============================================================
    def get_shipping_products(self, status: int = 1) -> list:
        """
        출고상품 조회 (벌크) - 전체 페이지 수집

        Args:
            status: 활성화 여부 (1=활성화)

        Returns:
            list: 출고상품 리스트
        """
        all_products = []
        page = 1

        while True:
            params = {'member_id': self.member_id, 'status': status, 'page': page}
            resp = self._request('GET', '/v2/product/shipping_products', params)

            if resp.get('code') != '9999':
                logger.warning(f"[출고상품조회] 실패: {resp.get('message')}")
                break

            response = resp.get('response', {})
            data_list = response.get('data_list', [])
            all_products.extend(data_list)

            total_page = int(response.get('total_page', 1))
            logger.info(f"[출고상품조회] 페이지 {page}/{total_page}: {len(data_list)}건")

            if page >= total_page:
                break
            page += 1
            time.sleep(0.3)

        logger.info(f"[출고상품조회] 완료: {len(all_products)}건")
        return all_products

    # ============================================================
    # 입고 API
    # ============================================================
    def get_receiving_plans(self, plan_date: str = None, plan_status: int = None) -> list:
        """
        입고예정 조회 (벌크) - 전체 페이지 수집

        Args:
            plan_date: 입고예정일 (YYYYMMDD)
            plan_status: 진행상태 (1:예정, 2:검수중, 3:완료, 4:취소)

        Returns:
            list: 입고예정 리스트
        """
        all_plans = []
        page = 1

        while True:
            params = {'member_id': self.member_id, 'page': page}
            if plan_date:
                params['plan_date'] = plan_date
            if plan_status is not None:
                params['plan_status'] = plan_status

            resp = self._request('GET', '/v2/inventory/receiving_plans', params)

            if resp.get('code') != '9999':
                logger.warning(f"[입고예정조회] 실패: {resp.get('message')}")
                break

            response = resp.get('response', {})
            data_list = response.get('data_list', [])
            all_plans.extend(data_list)

            total_page = int(response.get('total_page', 1))
            if page >= total_page:
                break
            page += 1
            time.sleep(0.3)

        logger.info(f"[입고예정조회] 완료: {len(all_plans)}건")
        return all_plans

    def get_receiving_plan_result(self, receiving_plan_id: int) -> dict:
        """
        예정대비입고현황 조회 (단일)

        Args:
            receiving_plan_id: 입고예정 ID

        Returns:
            dict: 예정 대비 입고 현황
        """
        params = {'member_id': self.member_id}
        resp = self._request('GET', f'/v2/inventory/receiving_plan_result/{receiving_plan_id}', params)

        if resp.get('code') != '9999':
            logger.warning(f"[예정대비입고] 실패 (plan_id={receiving_plan_id}): {resp.get('message')}")
            return {}

        return resp.get('response', {})

    def get_receiving_works(self, start_dt: str, end_dt: str, work_type: int = None) -> list:
        """
        입고작업내역 조회 (벌크) - 전체 페이지 수집

        Args:
            start_dt: 시작일 (YYYYMMDD)
            end_dt: 종료일 (YYYYMMDD)
            work_type: 작업구분 (1:입고, 3:적치, 5:회송, 7:반품입고, 9:취소)

        Returns:
            list: 작업내역 리스트
        """
        all_works = []
        page = 1

        while True:
            params = {
                'member_id': self.member_id,
                'start_dt': start_dt,
                'end_dt': end_dt,
                'page': page
            }
            if work_type is not None:
                params['work_type'] = work_type

            resp = self._request('GET', '/v2/inventory/receiving_works', params)

            if resp.get('code') != '9999':
                logger.warning(f"[입고작업내역] 실패: {resp.get('message')}")
                break

            response = resp.get('response', {})
            data_list = response.get('data_list', [])
            all_works.extend(data_list)

            total_page = int(response.get('total_page', 1))
            if page >= total_page:
                break
            page += 1
            time.sleep(0.3)

        logger.info(f"[입고작업내역] 완료: {len(all_works)}건")
        return all_works
