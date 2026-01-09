"""
Azure Blob Storage 관리 모듈
Request XML 업로드 및 Response JSON 저장
"""
import json
import logging
from typing import Optional
from azure.storage.blob import BlobServiceClient, BlobClient, ContentSettings, PublicAccess, BlobSasPermissions, generate_blob_sas
from datetime import timedelta
from .config import AZURE_BLOB_CONFIG, get_current_timestamp

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AzureBlobManager:
    """Azure Blob Storage 관리 클래스"""
    
    def __init__(self):
        """초기화"""
        self.connection_string = AZURE_BLOB_CONFIG['connection_string']
        self.container_name = AZURE_BLOB_CONFIG['container_name']
        
        if not self.connection_string:
            raise ValueError("Azure Storage Connection String이 설정되지 않았습니다.")
        
        try:
            # BlobServiceClient 생성
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            
            # Container 존재 확인 및 생성
            self.container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            
            if not self.container_client.exists():
                logger.info(f"Container '{self.container_name}' 생성 중...")
                self.container_client.create_container(public_access=PublicAccess.Blob)
                logger.info(f"Container '{self.container_name}' 생성 완료")
            else:
                logger.info(f"Container '{self.container_name}' 확인 완료")
                
        except Exception as e:
            logger.error(f"Azure Blob Storage 초기화 오류: {str(e)}")
            raise
    
    def upload_request_xml(self, xml_content: str, filename: Optional[str] = None) -> str:
        """
        Request XML을 Blob Storage에 업로드하고 SAS 토큰 URL 생성
        
        Args:
            xml_content: XML 문자열
            filename: 파일명 (없으면 자동 생성)
        
        Returns:
            str: SAS 토큰이 포함된 Blob URL
        """
        try:
            # 파일명 생성
            if filename is None:
                timestamp = get_current_timestamp()
                filename = f"request_{timestamp}.xml"
            
            # BlobClient 생성
            blob_client = self.container_client.get_blob_client(filename)
            
            # XML을 EUC-KR로 인코딩하여 업로드
            xml_bytes = xml_content.encode('euc-kr')
            
            # Content-Type 설정
            content_settings = ContentSettings(content_type='application/xml')
            
            # 업로드
            blob_client.upload_blob(
                xml_bytes,
                overwrite=True,
                content_settings=content_settings
            )
            
            # SAS 토큰 URL 생성 (1시간 유효)
            sas_url = self.generate_sas_url(filename, hours=1)
            logger.info(f"Request XML 업로드 완료: {filename}")
            logger.info(f"SAS URL 생성: {sas_url[:100]}...")
            
            return sas_url
            
        except Exception as e:
            logger.error(f"Request XML 업로드 오류: {str(e)}")
            raise
    
    def upload_response_json(self, data: dict, filename: Optional[str] = None) -> str:
        """
        Response JSON을 Blob Storage에 업로드
        
        Args:
            data: 저장할 데이터 (dict)
            filename: 파일명 (없으면 자동 생성)
        
        Returns:
            str: Blob URL
        """
        try:
            # 파일명 생성
            if filename is None:
                timestamp = get_current_timestamp()
                filename = f"orders_{timestamp}.json"
            
            # BlobClient 생성
            blob_client = self.container_client.get_blob_client(filename)
            
            # JSON 문자열로 변환
            json_string = json.dumps(data, ensure_ascii=False, indent=2)
            json_bytes = json_string.encode('utf-8')
            
            # Content-Type 설정
            content_settings = ContentSettings(content_type='application/json')
            
            # 업로드
            blob_client.upload_blob(
                json_bytes,
                overwrite=True,
                content_settings=content_settings
            )
            
            # URL 반환
            blob_url = blob_client.url
            logger.info(f"Response JSON 업로드 완료: {blob_url}")
            
            return blob_url
            
        except Exception as e:
            logger.error(f"Response JSON 업로드 오류: {str(e)}")
            raise
    
    def download_json(self, filename: str) -> dict:
        """
        Blob Storage에서 JSON 다운로드
        
        Args:
            filename: 파일명
        
        Returns:
            dict: JSON 데이터
        """
        try:
            blob_client = self.container_client.get_blob_client(filename)
            
            # 다운로드
            download_stream = blob_client.download_blob()
            json_string = download_stream.readall().decode('utf-8')
            
            # JSON 파싱
            data = json.loads(json_string)
            
            logger.info(f"JSON 다운로드 완료: {filename}")
            return data
            
        except Exception as e:
            logger.error(f"JSON 다운로드 오류: {str(e)}")
            raise
    
    def list_blobs(self, prefix: Optional[str] = None) -> list:
        """
        Container의 Blob 목록 조회
        
        Args:
            prefix: 접두사 필터 (없으면 전체)
        
        Returns:
            list: Blob 이름 목록
        """
        try:
            blobs = []
            for blob in self.container_client.list_blobs(name_starts_with=prefix):
                blobs.append({
                    'name': blob.name,
                    'size': blob.size,
                    'last_modified': blob.last_modified.isoformat(),
                })
            
            logger.info(f"Blob 목록 조회 완료: {len(blobs)}개")
            return blobs
            
        except Exception as e:
            logger.error(f"Blob 목록 조회 오류: {str(e)}")
            raise
    
    def delete_blob(self, filename: str) -> None:
        """
        Blob 삭제
        
        Args:
            filename: 파일명
        """
        try:
            blob_client = self.container_client.get_blob_client(filename)
            blob_client.delete_blob()
            
            logger.info(f"Blob 삭제 완료: {filename}")
            
        except Exception as e:
            logger.error(f"Blob 삭제 오류: {str(e)}")
            raise
    
    def generate_sas_url(self, filename: str, hours: int = 1) -> str:
        """
        Blob에 대한 SAS 토큰 URL 생성
        
        Args:
            filename: 파일명
            hours: SAS 토큰 유효 시간 (시간)
        
        Returns:
            str: SAS 토큰이 포함된 완전한 URL
        """
        try:
            from datetime import datetime, timezone
            
            # Storage Account 이름과 키 추출
            # Connection String에서 파싱
            conn_parts = dict(item.split('=', 1) for item in self.connection_string.split(';') if '=' in item)
            account_name = conn_parts.get('AccountName')
            account_key = conn_parts.get('AccountKey')
            
            if not account_name or not account_key:
                raise ValueError("Connection String에서 AccountName 또는 AccountKey를 찾을 수 없습니다.")
            
            # SAS 토큰 생성
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=self.container_name,
                blob_name=filename,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),  # 읽기 권한만
                expiry=datetime.now(timezone.utc) + timedelta(hours=hours)  # 유효기간
            )
            
            # 완전한 URL 구성
            blob_client = self.container_client.get_blob_client(filename)
            sas_url = f"{blob_client.url}?{sas_token}"
            
            return sas_url
            
        except Exception as e:
            logger.error(f"SAS URL 생성 오류: {str(e)}")
            raise


if __name__ == '__main__':
    # 테스트 코드
    blob_manager = AzureBlobManager()
    
    # Blob 목록 조회
    print("=" * 80)
    print("Blob 목록:")
    print("=" * 80)
    blobs = blob_manager.list_blobs()
    for blob in blobs:
        print(f"- {blob['name']} ({blob['size']} bytes, {blob['last_modified']})")
    print("=" * 80)
