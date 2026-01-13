"""
네이버 검색광고 AD 리포트 수집 모듈
AD + AD_CONVERSION 리포트 통합 수집
"""

import requests
import time
from datetime import datetime
from urllib.parse import urlparse
from .auth import NaverAuth

BASE_URL = "https://api.naver.com"


class NaverADReportFetcher:
    """AD + AD_CONVERSION 리포트 통합 수집"""

    def __init__(self):
        self.auth = NaverAuth()
        self.base_url = BASE_URL

    def fetch_ad_report_data(self, target_date: str) -> list:
        """
        특정 날짜의 AD + AD_CONVERSION 리포트 데이터 통합 수집
        
        Args:
            target_date: 날짜 (YYYY-MM-DD 형식)
        
        Returns:
            list: 파싱된 통합 데이터 리스트
        """
        date_obj = datetime.strptime(target_date, '%Y-%m-%d')
        stat_dt = date_obj.strftime('%Y%m%d')

        print(f"\n[통합 리포트 수집] {target_date}")

        # 1. AD 리포트 수집
        ad_data = self._fetch_report('AD', stat_dt, target_date)

        # 2. AD_CONVERSION 리포트 수집
        conversion_data = self._fetch_report('AD_CONVERSION', stat_dt, target_date)

        # 3. 데이터 통합
        merged_data = self._merge_reports(ad_data, conversion_data, target_date)

        print(f"   [통합 완료] {len(merged_data)}건")

        return merged_data

    def _fetch_report(self, report_type: str, stat_dt: str, target_date: str) -> list:
        """특정 타입의 리포트 수집"""
        print(f"\n   📊 [{report_type}] 리포트 수집 시작...")

        # 1. 리포트 생성
        report_job_id = self._create_report(report_type, stat_dt)
        if not report_job_id:
            print(f"      ❌ 리포트 생성 단계 실패")
            return []

        # 2. 리포트 완료 대기
        report_info = self._wait_for_report(report_job_id, max_wait=120)
        if not report_info or report_info.get('status') != 'BUILT':
            print(f"      ❌ 리포트 빌드 단계 실패")
            return []

        # 3. 다운로드
        download_url = report_info.get('downloadUrl')
        if not download_url:
            print(f"      ❌ 다운로드 URL 없음")
            print(f"         report_info: {report_info}")
            return []

        tsv_data = self._download_report(download_url)
        if not tsv_data:
            print(f"      ❌ 다운로드 단계 실패")
            return []

        # 4. 파싱
        if report_type == 'AD':
            parsed_data = self._parse_ad_tsv(tsv_data, target_date)
        else:
            parsed_data = self._parse_conversion_tsv(tsv_data, target_date)

        print(f"      ✓ 파싱 완료: {len(parsed_data)}건")

        return parsed_data

    def _create_report(self, report_type: str, stat_dt: str):
        """리포트 생성 요청"""
        uri = '/stat-reports'
        headers = self.auth.get_headers('POST', uri)

        report_data = {
            'reportTp': report_type,
            'statDt': stat_dt
        }

        try:
            response = requests.post(
                f"{self.base_url}{uri}",
                headers=headers,
                json=report_data,
                timeout=10
            )

            if response.status_code in [200, 201]:
                result = response.json()
                report_job_id = result.get('reportJobId')
                print(f"   ✓ 리포트 생성: {report_job_id}")
                return report_job_id
            else:
                print(f"   ❌ 리포트 생성 실패: {response.status_code}")
                print(f"      응답: {response.text}")
                return None

        except Exception as e:
            print(f"   ❌ 리포트 생성 예외: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _wait_for_report(self, report_job_id: str, max_wait: int = 120):
        """리포트 생성 완료 대기"""
        uri = f'/stat-reports/{report_job_id}'
        wait_interval = 3

        print(f"   ⏳ 리포트 빌드 대기 중 (최대 {max_wait}초)...")

        for elapsed in range(0, max_wait, wait_interval):
            time.sleep(wait_interval)

            headers = self.auth.get_headers('GET', uri)

            try:
                response = requests.get(
                    f"{self.base_url}{uri}",
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 200:
                    report_info = response.json()
                    status = report_info.get('status')

                    if status == 'BUILT':
                        print(f"   ✓ 리포트 완료 ({elapsed + wait_interval}초)")
                        return report_info
                    elif status == 'FAIL':
                        print(f"   ❌ 리포트 빌드 실패 (status=FAIL)")
                        print(f"      응답: {report_info}")
                        return None
                    elif status in ['REGIST', 'RUNNING']:
                        # 진행 중
                        if (elapsed + wait_interval) % 15 == 0:
                            print(f"      진행 중... ({elapsed + wait_interval}초 경과, status={status})")
                else:
                    print(f"   ❌ 상태 조회 실패: {response.status_code}")
                    print(f"      응답: {response.text}")

            except Exception as e:
                print(f"   ⚠️  상태 조회 예외: {e}")
                pass

        print(f"   ❌ 타임아웃 ({max_wait}초) - 리포트 생성이 완료되지 않음")
        return None

    def _download_report(self, download_url: str):
        """리포트 다운로드"""
        try:
            parsed = urlparse(download_url)
            download_uri = parsed.path

            headers = self.auth.get_headers('GET', download_uri)

            response = requests.get(
                download_url,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                print(f"   ✓ 다운로드 완료 ({len(response.text)} bytes)")
                return response.text
            else:
                print(f"   ❌ 다운로드 실패: {response.status_code}")
                print(f"      응답: {response.text}")
                return None

        except Exception as e:
            print(f"   ❌ 다운로드 예외: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _parse_ad_tsv(self, tsv_data: str, target_date: str) -> list:
        """AD 리포트 TSV 데이터 파싱"""
        lines = tsv_data.strip().split('\n')
        parsed_data = []

        for line in lines:
            if not line.strip():
                continue

            columns = line.split('\t')
            if len(columns) < 14:
                continue

            try:
                key = f"{columns[2]}_{columns[3]}_{columns[4]}_{columns[5]}_{columns[8]}"

                row = {
                    'key': key,
                    'Date': target_date,
                    'CampaignID': columns[2],
                    'AdGroupID': columns[3],
                    'KeywordID': columns[4],
                    'AdID': columns[5],
                    'Device': columns[8],
                    'Impressions': int(columns[9]) if columns[9].isdigit() else 0,
                    'Clicks': int(columns[10]) if columns[10].isdigit() else 0,
                }

                parsed_data.append(row)

            except (ValueError, IndexError):
                continue

        return parsed_data

    def _parse_conversion_tsv(self, tsv_data: str, target_date: str) -> list:
        """AD_CONVERSION 리포트 TSV 데이터 파싱"""
        lines = tsv_data.strip().split('\n')
        parsed_data = []

        for line in lines:
            if not line.strip():
                continue

            columns = line.split('\t')
            if len(columns) < 13:
                continue

            try:
                key = f"{columns[2]}_{columns[3]}_{columns[4]}_{columns[5]}_{columns[8]}_{columns[10]}"

                row = {
                    'key': key,
                    'Date': target_date,
                    'CampaignID': columns[2],
                    'AdGroupID': columns[3],
                    'KeywordID': columns[4],
                    'AdID': columns[5],
                    'Device': columns[8],
                    'ConversionType': columns[10],
                    'Conversions': int(columns[11]) if columns[11].isdigit() else 0,
                    'ConversionValue': int(columns[12]) if columns[12].isdigit() else 0,
                }

                parsed_data.append(row)

            except (ValueError, IndexError):
                continue

        return parsed_data

    def _merge_reports(self, ad_data: list, conversion_data: list, target_date: str) -> list:
        """AD 리포트와 AD_CONVERSION 리포트 통합"""
        ad_map = {item['key']: item for item in ad_data}

        conversion_map = {}
        for item in conversion_data:
            base_key = f"{item['CampaignID']}_{item['AdGroupID']}_{item['KeywordID']}_{item['AdID']}_{item['Device']}"

            if base_key not in conversion_map:
                conversion_map[base_key] = []

            conversion_map[base_key].append({
                'ConversionType': item['ConversionType'],
                'Conversions': item['Conversions'],
                'ConversionValue': item['ConversionValue']
            })

        merged = []

        for key, ad_item in ad_map.items():
            row = {
                'Date': target_date,
                'CampaignID': ad_item['CampaignID'],
                'AdGroupID': ad_item['AdGroupID'],
                'KeywordID': ad_item['KeywordID'],
                'AdID': ad_item['AdID'],
                'Device': ad_item['Device'],
                'Impressions': ad_item['Impressions'],
                'Clicks': ad_item['Clicks'],
            }

            # purchase 전환만 집계
            if key in conversion_map:
                conversions = conversion_map[key]
                purchase_conv = sum(c['Conversions'] for c in conversions if c['ConversionType'] == 'purchase')
                purchase_revenue = sum(c['ConversionValue'] for c in conversions if c['ConversionType'] == 'purchase')

                row['Conversions'] = purchase_conv
                row['ConversionValue'] = purchase_revenue
            else:
                row['Conversions'] = 0
                row['ConversionValue'] = 0

            merged.append(row)

        return merged
