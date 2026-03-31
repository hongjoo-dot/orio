"""
Azure Blob Storage 업로드 모듈 (Frog Cafe24)
출고 완료 주문 데이터를 JSON으로 저장
"""

import json
import os
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from .config import BLOB_CONTAINER, BLOB_PREFIX


class BlobUploader:
    """Azure Blob Storage 업로더 (Frog Cafe24)"""

    def __init__(self, connection_string=None):
        if not connection_string:
            connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

        if not connection_string:
            raise Exception("Azure Storage 연결 문자열이 없습니다.")

        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_name = BLOB_CONTAINER

    def upload_shipped_orders(self, orders_data, shipped_date):
        """출고 완료 주문 데이터를 Blob에 업로드"""
        if BLOB_PREFIX:
            blob_name = f"{BLOB_PREFIX}/{shipped_date}.json"
        else:
            blob_name = f"{shipped_date}.json"

        data = {
            "shipped_date": shipped_date,
            "collected_at": datetime.now().isoformat(),
            "total_orders": len(orders_data),
            "orders": orders_data
        }

        json_data = json.dumps(data, ensure_ascii=False, indent=2)

        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )

        blob_client.upload_blob(json_data, overwrite=True)

        blob_url = blob_client.url
        print(f"[Frog Cafe24 Blob 업로드 완료] {blob_url}")

        return blob_url
