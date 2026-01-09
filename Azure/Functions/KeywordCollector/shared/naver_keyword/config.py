from common.system_config import get_config

# API 인증 정보 (SystemConfig에서 읽기)
config = get_config()

CUSTOMER_ID = config.get('NaverKeywordAPI', 'customer_id')
ACCESS_LICENSE = config.get('NaverKeywordAPI', 'access_license')
SECRET_KEY = config.get('NaverKeywordAPI', 'secret_key')

# API 엔드포인트
BASE_URL = "https://api.searchad.naver.com"
KEYWORDSTOOL_PATH = "/keywordstool"
