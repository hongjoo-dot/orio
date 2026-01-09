"""
사방넷 주문 데이터 DB 업로드
- SabangnetOrders: 주문 마스터 (BA0 기준)
- SabangnetOrdersDetail: 구성품 상세 (모든 행)
"""
import sys
import os
import json
import pyodbc
from datetime import datetime
from collections import defaultdict, Counter
import logging

# 경로 설정
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common.database import get_db_connection

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SabangnetUploader:
    def __init__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        
        # 매핑 데이터 로드
        self.sabangnet_channel_map = {}  # {SabangnetMallID: ChannelID}
        self.product_map = {}            # {SabangnetCode: ProductID}
        self.bom_map = {}                # {frozenset([(ProductID, Qty), ...]): ParentProductID}
        
    def load_metadata(self):
        """메타데이터 로드 (Channel, Product, BOM)"""
        logger.info("메타데이터 로딩 중...")
        
        # 1. Channel 매핑 로드 (SabangnetMallID 기반)
        # ','로 구분된 복수 MallID 지원
        self.cursor.execute("SELECT ChannelID, SabangnetMallID FROM Channel WHERE SabangnetMallID IS NOT NULL")
        for channel_id, sabangnet_mall_id in self.cursor.fetchall():
            if sabangnet_mall_id:
                # ','로 분할 후 각각 매핑
                mall_ids = [mid.strip() for mid in sabangnet_mall_id.split(',')]
                for mall_id in mall_ids:
                    if mall_id:  # 빈 문자열 제외
                        self.sabangnet_channel_map[mall_id] = channel_id
        logger.info(f"Sabangnet Channel 매핑: {len(self.sabangnet_channel_map)}개 (MallID 총 개수)")
        
        # 2. Product 매핑 로드
        self.cursor.execute("SELECT ProductID, SabangnetCode FROM Product WHERE SabangnetCode IS NOT NULL")
        for product_id, code in self.cursor.fetchall():
            if code:
                self.product_map[code.strip()] = product_id
        logger.info(f"Product 매핑: {len(self.product_map)}개")
        
        # 3. BOM 매핑 로드 (BoxID 기반)
        # ProductID -> BoxID 매핑 (구성품용)
        self.product_to_boxes = defaultdict(list)
        self.cursor.execute("SELECT ProductID, BoxID FROM ProductBox")
        for product_id, box_id in self.cursor.fetchall():
            self.product_to_boxes[product_id].append(box_id)
        
        # ParentProductBoxID별로 {ChildProductBoxID: QuantityRequired} 구조 생성
        parent_box_to_children = defaultdict(dict)
        self.cursor.execute("""
            SELECT ParentProductBoxID, ChildProductBoxID, QuantityRequired 
            FROM ProductBOM
        """)
        for parent_box_id, child_box_id, qty_req in self.cursor.fetchall():
            parent_box_to_children[parent_box_id][child_box_id] = qty_req or 1
        
        # frozenset([(ChildBoxID, Qty)]) -> ParentProductBoxID 매핑
        self.bom_box_map = {}
        for parent_box_id, children_dict in parent_box_to_children.items():
            box_composition_key = frozenset(children_dict.items())
            self.bom_box_map[box_composition_key] = parent_box_id
        
        # ParentProductBoxID -> ParentProductID 매핑
        self.parent_box_to_product = {}
        self.cursor.execute("SELECT BoxID, ProductID FROM ProductBox")
        for box_id, product_id in self.cursor.fetchall():
            self.parent_box_to_product[box_id] = product_id
        
        logger.info(f"BOM 매핑: {len(self.bom_box_map)}개")

    def get_channel_id(self, mall_id):
        """MALL_ID -> ChannelID 변환 (DB의 SabangnetMallID 기반)"""
        if not mall_id:
            return None

        return self.sabangnet_channel_map.get(mall_id.strip())

    def get_product_id(self, sabangnet_code):
        """사방넷 코드 -> ProductID 변환"""
        if not sabangnet_code:
            return None
        return self.product_map.get(sabangnet_code.strip())

    def find_parent_product_id(self, composition_dict):
        """
        구성품 조합으로 부모 ProductID 찾기 (BoxID 기반)
        
        Args:
            composition_dict: {ProductID: 수량} 딕셔너리
        
        Returns:
            int or None: 부모 ProductID
        """
        if not composition_dict:
            return None
        
        # ProductID -> BoxID 변환 후 매칭 시도
        # ProductBOM에 등록된 ChildProductBoxID를 찾기 위해
        # 모든 가능한 BoxID 조합 시도
        from itertools import product as itertools_product
        
        # 각 ProductID에 대해 가능한 BoxID 리스트 수집
        product_ids = list(composition_dict.keys())
        possible_boxes = []
        for pid in product_ids:
            boxes = self.product_to_boxes.get(pid, [])
            if not boxes:
                return None  # BoxID가 없으면 매칭 불가
            possible_boxes.append(boxes)
        
        # 모든 BoxID 조합 시도
        for box_combination in itertools_product(*possible_boxes):
            # {BoxID: Qty} 딕셔너리 생성
            box_composition = {}
            for i, box_id in enumerate(box_combination):
                qty = composition_dict[product_ids[i]]
                box_composition[box_id] = qty
            
            # BoxID 조합으로 BOM 매칭
            box_composition_key = frozenset(box_composition.items())
            parent_box_id = self.bom_box_map.get(box_composition_key)
            
            if parent_box_id:
                # ParentProductBoxID -> ParentProductID 변환
                parent_product_id = self.parent_box_to_product.get(parent_box_id)
                return parent_product_id
        
        return None  # 매칭 실패

    def upload_json(self, data_or_path, blob_filename=None):
        """JSON 데이터를 DB에 업로드

        Args:
            data_or_path: JSON 파일 경로(str) 또는 JSON 데이터(dict)
            blob_filename: Blob 파일명 (data_or_path가 dict일 때 사용)
        """
        try:
            # 데이터 로드
            if isinstance(data_or_path, str):
                json_path = data_or_path
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 파일명만 추출 (경로 제거)
                blob_path = os.path.basename(json_path)
            else:
                data = data_or_path
                json_path = blob_filename or "Blob Storage Data"
                blob_path = blob_filename or "Blob Storage Data"

            orders = data.get('orders', [])
            if not orders:
                logger.warning("업로드할 주문 데이터가 없습니다.")
                return

            logger.info(f"총 {len(orders)}건의 주문 데이터 처리 시작")
            
            # 트랜잭션 시작
            self.conn.autocommit = False
            
            # ORDER_ID -> MALL_PRODUCT_ID로 2단계 그룹핑
            # (MALL_ORDER_SEQ 데이터는 수집하지만 아직 그룹핑에는 사용하지 않음)
            # grouped_orders[order_id][mall_product_id] = [items...]
            grouped_orders = defaultdict(lambda: defaultdict(list))
            
            for order in orders:
                order_id = order.get('ORDER_ID')
                mall_product_id = order.get('MALL_PRODUCT_ID')
                
                # 기존 방식 유지: MALL_PRODUCT_ID로 그룹핑
                if order_id and mall_product_id:
                    grouped_orders[order_id][mall_product_id].append(order)
            
            # ==========================================
            # 1. SabangnetOrdersDetail 업로드
            # ==========================================
            detail_values = []
            
            for order in orders:
                # ProductID 매핑
                product_id = self.get_product_id(order.get('PRODUCT_ID'))
                
                row = (
                    int(order.get('IDX', 0)),
                    order.get('ORDER_ID'),
                    order.get('MALL_PRODUCT_ID'),
                    order.get('PRODUCT_NAME'),
                    order.get('PRODUCT_ID'),
                    product_id,
                    order.get('P_PRODUCT_NAME'),
                    order.get('SKU_ID'),
                    int(order.get('SALE_CNT', 0) or 0),
                    order.get('ord_field2'),
                )
                detail_values.append(row)

            # MERGE 방식: IDX 기준으로 UPDATE 또는 INSERT
            # OUTPUT 절로 INSERT/UPDATE 구분
            detail_query = """
            MERGE INTO SabangnetOrdersDetail AS target
            USING (SELECT ? AS IDX, ? AS ORDER_ID, ? AS MALL_PRODUCT_ID, ? AS PRODUCT_NAME,
                          ? AS PRODUCT_ID, ? AS ProductID, ? AS P_PRODUCT_NAME,
                          ? AS SKU_ID, ? AS SALE_CNT, ? AS ord_field2) AS source
            ON target.IDX = source.IDX
            WHEN MATCHED THEN
                UPDATE SET
                    ORDER_ID = source.ORDER_ID,
                    MALL_PRODUCT_ID = source.MALL_PRODUCT_ID,
                    PRODUCT_NAME = source.PRODUCT_NAME,
                    PRODUCT_ID = source.PRODUCT_ID,
                    ProductID = source.ProductID,
                    P_PRODUCT_NAME = source.P_PRODUCT_NAME,
                    SKU_ID = source.SKU_ID,
                    SALE_CNT = source.SALE_CNT,
                    ord_field2 = source.ord_field2
            WHEN NOT MATCHED THEN
                INSERT (IDX, ORDER_ID, MALL_PRODUCT_ID, PRODUCT_NAME, PRODUCT_ID, ProductID,
                        P_PRODUCT_NAME, SKU_ID, SALE_CNT, ord_field2)
                VALUES (source.IDX, source.ORDER_ID, source.MALL_PRODUCT_ID, source.PRODUCT_NAME,
                        source.PRODUCT_ID, source.ProductID, source.P_PRODUCT_NAME,
                        source.SKU_ID, source.SALE_CNT, source.ord_field2)
            OUTPUT $action;
            """

            detail_inserted = 0
            detail_updated = 0
            detail_inserted = 0
            detail_updated = 0
            for i, detail_row in enumerate(detail_values):
                self.cursor.execute(detail_query, detail_row)
                result = self.cursor.fetchone()
                if result:
                    action = result[0]
                    if action == 'INSERT':
                        detail_inserted += 1
                    elif action == 'UPDATE':
                        detail_updated += 1
                
                # 배치 커밋 (1000건마다)
                if (i + 1) % 1000 == 0:
                    self.conn.commit()
                    logger.info(f"  - Detail {i + 1}건 처리 중...")

            logger.info(f"✅ SabangnetOrdersDetail: INSERT {detail_inserted}건, UPDATE {detail_updated}건")
            
            # ==========================================
            # 2. SabangnetOrders 업로드
            # ==========================================
            master_values = []
            
            # 주문별 -> 상품별 순회
            for order_id, mall_products in grouped_orders.items():
                for mall_product_id, items in mall_products.items():
                    
                    # ======================================================================
                    # 3단계 그룹핑 필요 여부 확인
                    # ======================================================================
                    # NULL(단품) 또는 BA0(세트 메인) 개수 확인
                    critical_items = [item for item in items if item.get('ord_field2') in [None, '', 'BA0']]
                    
                    if len(critical_items) >= 2:
                        # ========== 3단계 그룹핑 필요 (여러 옵션이 한번에 주문됨) ==========
                        logger.info(f"3단계 그룹핑: ORDER_ID {order_id}, MALL_PID {mall_product_id} (항목 {len(critical_items)}개)")
                        
                        # 단품 처리 (ord_field2 = NULL)
                        null_items = [item for item in items if item.get('ord_field2') in [None, '']]
                        for null_item in null_items:
                            product_id = self.get_product_id(null_item.get('PRODUCT_ID'))
                            parent_product_id = product_id
                            sale_cnt = int(null_item.get('SALE_CNT', 1) or 1)
                            
                            # ChannelID 매핑
                            channel_id = self.get_channel_id(null_item.get('MALL_ID'))
                            
                            # ORDER_DATE 처리
                            order_date_str = null_item.get('ORDER_DATE', '')
                            try:
                                order_date = datetime.strptime(order_date_str, '%Y%m%d%H%M%S')
                            except:
                                order_date = datetime.now()

                            # DELIVERY_CONFIRM_DATE 처리
                            delivery_confirm_date = None
                            delivery_confirm_str = null_item.get('DELIVERY_CONFIRM_DATE', '')
                            if delivery_confirm_str:
                                try:
                                    delivery_confirm_date = datetime.strptime(delivery_confirm_str, '%Y%m%d%H%M%S')
                                except:
                                    delivery_confirm_date = None

                            row = (
                                int(null_item.get('IDX', 0)),
                                null_item.get('ORDER_ID'),
                                order_date,
                                null_item.get('ORDER_STATUS'),
                                null_item.get('MALL_ID'),
                                channel_id,
                                null_item.get('USER_NAME'),
                                null_item.get('USER_TEL'),
                                null_item.get('RECEIVE_TEL'),
                                sale_cnt,
                                float(null_item.get('PAY_COST', 0) or 0),
                                float(null_item.get('DELV_COST', 0) or 0),
                                null_item.get('DELIVERY_METHOD_STR'),
                                delivery_confirm_date,
                                null_item.get('BRAND_NM'),
                                parent_product_id,
                                null_item.get('SET_GUBUN'),
                                blob_path,
                            )
                            master_values.append(row)
                        
                        # 세트 처리 (ord_field2 = BA0/BB0): GOODS_NM_PR로 그룹핑
                        set_items = [item for item in items if item.get('ord_field2') in ['BA0', 'BB0']]
                        goods_nm_groups = defaultdict(list)
                        for item in set_items:
                            goods_nm = item.get('GOODS_NM_PR', '')
                            if goods_nm:  # GOODS_NM_PR가 있는 것만
                                goods_nm_groups[goods_nm].append(item)
                        
                        # 각 GOODS_NM_PR 그룹별로 세트 매칭
                        for goods_nm, group_items in goods_nm_groups.items():
                            # BA0 개수 카운트
                            ba0_count = sum(1 for item in group_items if item.get('ord_field2') == 'BA0')
                            
                            if ba0_count == 0:
                                continue  # BA0 없으면 스킵
                            
                            # 대표 아이템 (BA0)
                            representative_item = next((item for item in group_items if item.get('ord_field2') == 'BA0'), group_items[0])
                            
                            # 구성품 집계
                            composition_dict = {}
                            for item in group_items:
                                if item.get('ord_field2') in ['BA0', 'BB0']:
                                    product_id = self.get_product_id(item.get('PRODUCT_ID'))
                                    if product_id:
                                        composition_dict[product_id] = composition_dict.get(product_id, 0) + 1
                            
                            # 정규화
                            normalized_composition = {}
                            for product_id, count in composition_dict.items():
                                normalized_count = count / ba0_count
                                if normalized_count != int(normalized_count):
                                    logger.warning(f"ORDER_ID {order_id}, GOODS_NM_PR '{goods_nm}': 구성품 수({count})가 BA0 개수({ba0_count})로 나누어떨어지지 않음")
                                normalized_composition[product_id] = int(normalized_count)
                            
                            # BOM 매칭
                            parent_product_id = self.find_parent_product_id(normalized_composition)
                            sale_cnt = ba0_count
                            
                            # ChannelID 매핑
                            channel_id = self.get_channel_id(representative_item.get('MALL_ID'))
                            
                            # ORDER_DATE 처리
                            order_date_str = representative_item.get('ORDER_DATE', '')
                            try:
                                order_date = datetime.strptime(order_date_str, '%Y%m%d%H%M%S')
                            except:
                                order_date = datetime.now()

                            # DELIVERY_CONFIRM_DATE 처리
                            delivery_confirm_date = None
                            delivery_confirm_str = representative_item.get('DELIVERY_CONFIRM_DATE', '')
                            if delivery_confirm_str:
                                try:
                                    delivery_confirm_date = datetime.strptime(delivery_confirm_str, '%Y%m%d%H%M%S')
                                except:
                                    delivery_confirm_date = None

                            row = (
                                int(representative_item.get('IDX', 0)),
                                representative_item.get('ORDER_ID'),
                                order_date,
                                representative_item.get('ORDER_STATUS'),
                                representative_item.get('MALL_ID'),
                                channel_id,
                                representative_item.get('USER_NAME'),
                                representative_item.get('USER_TEL'),
                                representative_item.get('RECEIVE_TEL'),
                                sale_cnt,
                                float(representative_item.get('PAY_COST', 0) or 0),
                                float(representative_item.get('DELV_COST', 0) or 0),
                                representative_item.get('DELIVERY_METHOD_STR'),
                                delivery_confirm_date,
                                representative_item.get('BRAND_NM'),
                                parent_product_id,
                                representative_item.get('SET_GUBUN'),
                                blob_path,
                            )
                            master_values.append(row)
                    
                    else:
                        # ========== 기존 2단계 로직 (단일 상품 또는 단일 세트) ==========
                        # BA0 행 개수 카운트 (세트 주문 수량)
                        ba0_count = sum(1 for item in items if item.get('ord_field2') == 'BA0')
                        
                        # 대표 아이템 선택 (BA0 우선, 없으면 첫 번째)
                        representative_item = next((item for item in items if item.get('ord_field2') == 'BA0'), items[0])
                        
                        if ba0_count == 0:
                            # ========== 단품 처리 ==========
                            # ProductID 직접 매핑
                            product_id = self.get_product_id(representative_item.get('PRODUCT_ID'))
                            parent_product_id = product_id  # 단품은 ProductID 그대로
                            sale_cnt = int(representative_item.get('SALE_CNT', 1) or 1)
                        else:
                            # ========== 세트 처리 ==========
                            # 구성품 수량 집계 (ord_field2가 NULL인 단품 제외, BA0/BB0만 포함)
                            composition_dict = {}
                            for item in items:
                                # 세트 구성품만 집계 (ord_field2가 BA0 또는 BB0인 것만)
                                if item.get('ord_field2') in ['BA0', 'BB0']:
                                    product_id = self.get_product_id(item.get('PRODUCT_ID'))
                                    if product_id:
                                        composition_dict[product_id] = composition_dict.get(product_id, 0) + 1
                            
                            # BA0 개수로 나누어 1세트 기준으로 정규화
                            normalized_composition = {}
                            for product_id, count in composition_dict.items():
                                normalized_count = count / ba0_count
                                # 정수로 떨어지지 않으면 문제가 있는 데이터
                                if normalized_count != int(normalized_count):
                                    logger.warning(f"ORDER_ID {order_id}, MALL_PID {mall_product_id}: 구성품 수({count})가 BA0 개수({ba0_count})로 나누어떨어지지 않음")
                                normalized_composition[product_id] = int(normalized_count)
                            
                            # 정규화된 구성으로 부모 ProductID 찾기
                            parent_product_id = self.find_parent_product_id(normalized_composition)
                            sale_cnt = ba0_count  # 세트 수량
                        
                        # ChannelID 매핑
                        channel_id = self.get_channel_id(representative_item.get('MALL_ID'))
                        
                        # ORDER_DATE 처리
                        order_date_str = representative_item.get('ORDER_DATE', '')
                        try:
                            order_date = datetime.strptime(order_date_str, '%Y%m%d%H%M%S')
                        except:
                            order_date = datetime.now()

                        # DELIVERY_CONFIRM_DATE 처리
                        delivery_confirm_date = None
                        delivery_confirm_str = representative_item.get('DELIVERY_CONFIRM_DATE', '')
                        if delivery_confirm_str:
                            try:
                                delivery_confirm_date = datetime.strptime(delivery_confirm_str, '%Y%m%d%H%M%S')
                            except:
                                delivery_confirm_date = None

                        row = (
                            int(representative_item.get('IDX', 0)),
                            representative_item.get('ORDER_ID'),
                            order_date,
                            representative_item.get('ORDER_STATUS'),
                            representative_item.get('MALL_ID'),
                            channel_id,
                            representative_item.get('USER_NAME'),
                            representative_item.get('USER_TEL'),
                            representative_item.get('RECEIVE_TEL'),
                            sale_cnt,  # 단품: SALE_CNT, 세트: BA0 개수
                            float(representative_item.get('PAY_COST', 0) or 0),
                            float(representative_item.get('DELV_COST', 0) or 0),
                            representative_item.get('DELIVERY_METHOD_STR'),
                            delivery_confirm_date,
                            representative_item.get('BRAND_NM'),
                            parent_product_id,
                            representative_item.get('SET_GUBUN'),
                            blob_path,
                        )
                        master_values.append(row)


            # MERGE 방식: IDX 기준으로 UPDATE 또는 INSERT
            # OUTPUT 절로 INSERT/UPDATE 구분
            master_query = """
            MERGE INTO SabangnetOrders AS target
            USING (SELECT ? AS IDX, ? AS ORDER_ID, ? AS ORDER_DATE, ? AS ORDER_STATUS,
                          ? AS MALL_ID, ? AS ChannelID, ? AS USER_NAME, ? AS USER_TEL,
                          ? AS RECEIVE_TEL, ? AS SALE_CNT, ? AS PAY_COST, ? AS DELV_COST,
                          ? AS DELIVERY_METHOD_STR, ? AS DELIVERY_CONFIRM_DATE, ? AS BRAND_NM,
                          ? AS ProductID, ? AS SET_GUBUN, ? AS BlobPath) AS source
            ON target.IDX = source.IDX
            WHEN MATCHED THEN
                UPDATE SET
                    ORDER_ID = source.ORDER_ID,
                    ORDER_DATE = source.ORDER_DATE,
                    ORDER_STATUS = source.ORDER_STATUS,
                    MALL_ID = source.MALL_ID,
                    ChannelID = source.ChannelID,
                    USER_NAME = source.USER_NAME,
                    USER_TEL = source.USER_TEL,
                    RECEIVE_TEL = source.RECEIVE_TEL,
                    SALE_CNT = source.SALE_CNT,
                    PAY_COST = source.PAY_COST,
                    DELV_COST = source.DELV_COST,
                    DELIVERY_METHOD_STR = source.DELIVERY_METHOD_STR,
                    DELIVERY_CONFIRM_DATE = source.DELIVERY_CONFIRM_DATE,
                    BRAND_NM = source.BRAND_NM,
                    ProductID = source.ProductID,
                    SET_GUBUN = source.SET_GUBUN,
                    BlobPath = source.BlobPath
            WHEN NOT MATCHED THEN
                INSERT (IDX, ORDER_ID, ORDER_DATE, ORDER_STATUS, MALL_ID, ChannelID,
                        USER_NAME, USER_TEL, RECEIVE_TEL, SALE_CNT, PAY_COST, DELV_COST,
                        DELIVERY_METHOD_STR, DELIVERY_CONFIRM_DATE, BRAND_NM, ProductID, SET_GUBUN, BlobPath)
                VALUES (source.IDX, source.ORDER_ID, source.ORDER_DATE, source.ORDER_STATUS,
                        source.MALL_ID, source.ChannelID, source.USER_NAME, source.USER_TEL,
                        source.RECEIVE_TEL, source.SALE_CNT, source.PAY_COST, source.DELV_COST,
                        source.DELIVERY_METHOD_STR, source.DELIVERY_CONFIRM_DATE, source.BRAND_NM,
                        source.ProductID, source.SET_GUBUN, source.BlobPath)
            OUTPUT $action;
            """

            master_inserted = 0
            master_updated = 0
            master_inserted = 0
            master_updated = 0
            for i, master_row in enumerate(master_values):
                self.cursor.execute(master_query, master_row)
                result = self.cursor.fetchone()
                if result:
                    action = result[0]
                    if action == 'INSERT':
                        master_inserted += 1
                    elif action == 'UPDATE':
                        master_updated += 1

                # 배치 커밋 (1000건마다)
                if (i + 1) % 1000 == 0:
                    self.conn.commit()
                    logger.info(f"  - Master {i + 1}건 처리 중...")

            logger.info(f"✅ SabangnetOrders: INSERT {master_inserted}건, UPDATE {master_updated}건")

            self.conn.commit()
            logger.info("✨ 트랜잭션 커밋 완료")

            # 매핑 실패 확인 및 슬랙 알림
            upload_stats = {
                'total_detail': len(detail_values),
                'detail_inserted': detail_inserted,
                'detail_updated': detail_updated,
                'total_master': len(master_values),
                'master_inserted': master_inserted,
                'master_updated': master_updated,
            }
            self._check_and_notify_failures(upload_stats, blob_path)

        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ 업로드 실패: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            self.cursor.close()
            self.conn.close()

    def _check_and_notify_failures(self, upload_stats, blob_path):
        """
        매핑 실패 확인 및 슬랙 알림

        Args:
            upload_stats: 업로드 통계 dict
            blob_path: 업로드한 JSON 파일명
        """
        try:
            from slack_notifier import send_slack_notification, format_upload_result

            # 새로운 커넥션으로 실패 건수 확인
            check_conn = get_db_connection()
            check_cursor = check_conn.cursor()

            # 1. 단품 매핑 실패: Detail에서 (ord_field2 IS NULL OR ord_field2 = '') & ProductID IS NULL
            check_cursor.execute("""
                SELECT COUNT(*)
                FROM SabangnetOrdersDetail d
                INNER JOIN SabangnetOrders o ON d.ORDER_ID = o.ORDER_ID
                WHERE (d.ord_field2 IS NULL OR d.ord_field2 = '')
                AND d.ProductID IS NULL
                AND o.BlobPath = ?
            """, blob_path)
            single_product_failures = check_cursor.fetchone()[0]

            # 2. BOM 매핑 실패: Orders에서 ProductID IS NULL & Detail에 BA0 있음
            check_cursor.execute("""
                SELECT COUNT(*)
                FROM SabangnetOrders
                WHERE ProductID IS NULL
                AND BlobPath = ?
                AND EXISTS (
                    SELECT 1 FROM SabangnetOrdersDetail d
                    WHERE d.ORDER_ID = SabangnetOrders.ORDER_ID
                    AND d.ord_field2 = 'BA0'
                )
            """, blob_path)
            bom_failures = check_cursor.fetchone()[0]

            check_cursor.close()
            check_conn.close()

            # 슬랙 알림 전송
            if single_product_failures > 0 or bom_failures > 0:
                logger.warning(f"매핑 실패 발견: 단품 {single_product_failures}건, BOM {bom_failures}건")

            slack_message = format_upload_result(
                upload_stats=upload_stats,
                single_product_failures=single_product_failures,
                bom_failures=bom_failures
            )
            send_slack_notification(slack_message)

        except Exception as e:
            logger.warning(f"슬랙 알림 전송 중 오류 (무시됨): {e}")


if __name__ == '__main__':
    uploader = SabangnetUploader()
    uploader.load_metadata()

    # Azure Blob에서 최신 JSON 다운로드 후 업로드
    from azure_blob import AzureBlobManager

    blob_manager = AzureBlobManager()

    # 최신 JSON 파일 찾기
    blobs = blob_manager.list_blobs(prefix='orders_')
    if not blobs:
        logger.error("Blob에 주문 데이터가 없습니다.")
        sys.exit(1)

    latest_blob = max(blobs, key=lambda x: x['last_modified'])
    logger.info(f"최신 JSON 파일: {latest_blob['name']} ({latest_blob['last_modified']})")

    json_data = blob_manager.download_json(latest_blob['name'])

    if json_data:
        uploader.upload_json(json_data, blob_filename=latest_blob['name'])
    else:
        logger.error("JSON 다운로드 실패")
