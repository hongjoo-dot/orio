
import sys
import os
import json

# 현재 디렉토리를 패키지로 인식하도록 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# local.settings.json에서 환경 변수 로드
settings_path = os.path.join(current_dir, 'local.settings.json')
if os.path.exists(settings_path):
    with open(settings_path, 'r') as f:
        settings = json.load(f)
        for key, value in settings.get('Values', {}).items():
            if not key.startswith('COMMENT'):
                os.environ[key] = value
    print("[OK] local.settings.json 환경 변수 로드 완료")

from shared.system_config import get_config

def check_config():
    config = get_config()
    print("Loaded Categories:", config._cache.keys())
    
    naver_config = config._cache.get('NaverAdAPI', {})
    print("NaverAdAPI Config:", naver_config)
    
    if 'CUSTOMER_ID' in naver_config:
        print("CUSTOMER_ID exists")
    else:
        print("CUSTOMER_ID MISSING")

if __name__ == "__main__":
    check_config()
