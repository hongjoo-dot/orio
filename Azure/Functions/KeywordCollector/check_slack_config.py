import sys
import os
import logging

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from common.system_config import get_config

def main():
    config = get_config()
    print("--- GoogleKeywordAPI ---")
    print(f"SLACK_WEBHOOK_URL: {config.get('GoogleKeywordAPI', 'SLACK_WEBHOOK_URL')}")
    
    print("\n--- NaverKeywordAPI ---")
    print(f"SLACK_WEBHOOK_URL: {config.get('NaverKeywordAPI', 'SLACK_WEBHOOK_URL')}")

if __name__ == "__main__":
    main()
