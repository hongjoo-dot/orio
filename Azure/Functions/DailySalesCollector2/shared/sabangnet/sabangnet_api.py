"""
사방넷 API 연동 모듈
주문수집 API를 통해 주문 데이터 수집
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import json
import logging
from typing import List, Dict, Optional
from .config import SABANGNET_CONFIG, ORDER_CONFIG

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SabangnetAPI:
    """사방넷 주문수집 API 클래스"""
    
    def __init__(self):
        """초기화"""
        self.company_id = SABANGNET_CONFIG['company_id']
        self.auth_key = SABANGNET_CONFIG['auth_key']
        self.api_url = SABANGNET_CONFIG['api_url']
        self.order_status = ORDER_CONFIG['order_status']
        self.order_fields = ORDER_CONFIG['order_fields']
    
    def create_request_xml(self, start_date: str, end_date: str) -> str:
        """
        사방넷 API Request XML 생성
        
        Args:
            start_date: 주문 시작일 (YYYYMMDD)
            end_date: 주문 종료일 (YYYYMMDD)
        
        Returns:
            str: XML 문자열
        """
        # 현재 날짜
        send_date = datetime.now().strftime('%Y%m%d')
        
        # 필드 목록을 파이프(|)로 구분
        ord_field = '|'.join(self.order_fields)
        
        # XML 생성
        root = ET.Element('SABANG_ORDER_LIST')
        
        # HEADER
        header = ET.SubElement(root, 'HEADER')
        ET.SubElement(header, 'SEND_COMPAYNY_ID').text = self.company_id
        ET.SubElement(header, 'SEND_AUTH_KEY').text = self.auth_key
        ET.SubElement(header, 'SEND_DATE').text = send_date
        
        # DATA
        data = ET.SubElement(root, 'DATA')
        ET.SubElement(data, 'ORD_ST_DATE').text = start_date
        ET.SubElement(data, 'ORD_ED_DATE').text = end_date
        ET.SubElement(data, 'ORD_FIELD').text = ord_field
        ET.SubElement(data, 'ORDER_STATUS').text = self.order_status
        
        # XML 문자열로 변환
        xml_string = ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')
        
        # EUC-KR로 인코딩 선언 변경
        xml_string = xml_string.replace('encoding=\'utf-8\'', 'encoding="EUC-KR"')
        
        logger.info(f"Request XML 생성 완료: {start_date} ~ {end_date}")
        return xml_string
    
    def parse_response_xml(self, xml_string: str) -> Dict:
        """
        사방넷 API Response XML 파싱
        
        Args:
            xml_string: 응답 XML 문자열
        
        Returns:
            dict: 파싱된 주문 데이터
        """
        try:
            from lxml import etree
            
            # XML 파서 생성 (huge_tree=True로 큰 XML 처리, recover=True로 오류 복구)
            parser = etree.XMLParser(huge_tree=True, recover=True, encoding='utf-8')
            
            # XML 파싱
            root = etree.fromstring(xml_string.encode('utf-8'), parser=parser)
            
            # HEADER 정보 추출
            header = root.find('HEADER')
            total_count = header.find('TOTAL_COUNT').text if header.find('TOTAL_COUNT') is not None else '0'
            
            # DATA 목록 추출
            orders = []
            for data in root.findall('DATA'):
                order = {}
                for field in self.order_fields:
                    element = data.find(field)
                    order[field] = element.text if element is not None and element.text else ''
                orders.append(order)
            
            result = {
                'header': {
                    'company_id': header.find('SEND_COMPAYNY_ID').text if header.find('SEND_COMPAYNY_ID') is not None else '',
                    'send_date': header.find('SEND_DATE').text if header.find('SEND_DATE') is not None else '',
                    'total_count': int(total_count),
                },
                'orders': orders,
                'collected_at': datetime.now().isoformat(),
            }
            
            logger.info(f"주문 데이터 파싱 완료: {total_count}건")
            return result
            
        except Exception as e:
            logger.error(f"XML 파싱 오류: {str(e)}")
            raise
    
    def fetch_orders(self, start_date: str, end_date: str, xml_url: str) -> Dict:
        """
        사방넷에서 주문 데이터 수집
        
        Args:
            start_date: 주문 시작일 (YYYYMMDD)
            end_date: 주문 종료일 (YYYYMMDD)
            xml_url: Request XML이 호스팅된 URL
        
        Returns:
            dict: 주문 데이터
        """
        try:
            # API URL 구성
            full_url = f"{self.api_url}?xml_url={xml_url}"
            
            logger.info(f"사방넷 API 호출: {full_url}")
            
            # API 호출
            response = requests.get(full_url, timeout=30)
            response.raise_for_status()
            
            # 응답 내용 로깅 (디버깅용)
            logger.info(f"응답 상태 코드: {response.status_code}")
            logger.info(f"응답 길이: {len(response.text)} bytes")
            
            # 응답 파싱
            result = self.parse_response_xml(response.text)
            
            logger.info(f"주문 데이터 수집 완료: {result['header']['total_count']}건")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API 호출 오류: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"주문 수집 오류: {str(e)}")
            raise
    
    def save_to_json(self, data: Dict, file_path: str) -> None:
        """
        주문 데이터를 JSON 파일로 저장
        
        Args:
            data: 주문 데이터
            file_path: 저장할 파일 경로
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"JSON 파일 저장 완료: {file_path}")
            
        except Exception as e:
            logger.error(f"JSON 저장 오류: {str(e)}")
            raise


if __name__ == '__main__':
    # 테스트 코드
    from config import get_date_range
    
    api = SabangnetAPI()
    
    # 7일치 날짜 범위 생성
    start_date, end_date = get_date_range(7)
    
    # Request XML 생성 및 출력
    request_xml = api.create_request_xml(start_date, end_date)
    print("=" * 80)
    print("Request XML:")
    print("=" * 80)
    print(request_xml)
    print("=" * 80)
