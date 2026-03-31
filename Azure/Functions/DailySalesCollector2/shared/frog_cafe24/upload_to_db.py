"""
Azure SQL Database 업로드 모듈 (Frog Cafe24)
MERGE 로직: order_id 기준으로 INSERT or UPDATE
ProductID 매핑 포함
"""

import os
import pyodbc
from datetime import datetime


class DatabaseUploader:
    """Azure SQL Database 업로더 (Frog Cafe24)"""

    def __init__(self):
        connection_string = self._get_connection_string()
        self.connection = pyodbc.connect(connection_string)
        self.cursor = self.connection.cursor()

    def _get_connection_string(self):
        server = os.getenv('DB_SERVER')
        database = os.getenv('DB_DATABASE')
        username = os.getenv('DB_USERNAME')
        password = os.getenv('DB_PASSWORD')
        driver = os.getenv('DB_DRIVER', '{ODBC Driver 18 for SQL Server}')

        if not all([server, database, username, password]):
            raise Exception("DB 연결 정보가 환경변수에 없습니다. (DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD)")

        return (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout=60;"
        )

    def merge_orders(self, orders_data):
        """주문 데이터를 DB에 MERGE"""
        inserted_orders = 0
        updated_orders = 0
        inserted_details = 0
        updated_details = 0

        total_items = 0
        product_id_mapped = 0
        product_id_not_mapped = 0
        unmapped_codes = []

        for order in orders_data:
            try:
                order_result, cafe24_order_id = self._merge_order(order)
                if order_result == "INSERT":
                    inserted_orders += 1
                elif order_result == "UPDATE":
                    updated_orders += 1

                items = order.get("items", [])
                for item in items:
                    total_items += 1
                    detail_result, product_id, unique_code = self._merge_order_detail(order, item, cafe24_order_id)

                    if detail_result == "INSERT":
                        inserted_details += 1
                    elif detail_result == "UPDATE":
                        updated_details += 1

                    if product_id is not None:
                        product_id_mapped += 1
                    else:
                        product_id_not_mapped += 1
                        if unique_code:
                            unmapped_codes.append(unique_code)

            except Exception as e:
                print(f"[ERROR] 주문 처리 실패 (order_id: {order.get('order_id')}): {e}")
                import traceback
                traceback.print_exc()
                continue

        self.connection.commit()

        result = {
            "inserted_orders": inserted_orders,
            "updated_orders": updated_orders,
            "inserted_details": inserted_details,
            "updated_details": updated_details,
            "total_items": total_items,
            "product_id_mapped": product_id_mapped,
            "product_id_not_mapped": product_id_not_mapped,
            "unmapped_codes": unmapped_codes
        }

        print(f"\n[Frog Cafe24 DB MERGE 완료]")
        print(f"  Orders: INSERT {inserted_orders}건, UPDATE {updated_orders}건")
        print(f"  Details: INSERT {inserted_details}건, UPDATE {updated_details}건")
        print(f"\n[ProductID 매핑]")
        print(f"  전체 아이템: {total_items}건")
        print(f"  매핑 성공: {product_id_mapped}건")
        print(f"  매핑 실패: {product_id_not_mapped}건")

        if product_id_not_mapped > 0:
            print(f"\n  [경고] {product_id_not_mapped}건의 아이템이 ProductID에 매핑되지 않았습니다!")
            unique_unmapped = list(set(unmapped_codes))[:10]
            print(f"  매핑 실패 코드 (최대 10개): {', '.join(unique_unmapped)}")

        return result

    def _merge_order(self, order):
        """FrogCafe24Orders 테이블 MERGE"""
        order_id = order.get("order_id")

        self.cursor.execute(
            "SELECT Cafe24OrderID FROM FrogCafe24Orders WHERE order_id = ?",
            (order_id,)
        )
        existing = self.cursor.fetchone()

        data = self._extract_order_data(order)

        if existing:
            cafe24_order_id = existing[0]
            self.cursor.execute("""
                UPDATE FrogCafe24Orders SET
                    order_date = ?,
                    payment_date = ?,
                    order_status = ?,
                    shipping_status = ?,
                    shipped_date = ?,
                    purchaseconfirmation_date = ?,
                    member_id = ?,
                    billing_name = ?,
                    member_email = ?,
                    order_place_name = ?,
                    order_from_mobile = ?,
                    order_price_amount = ?,
                    shipping_fee = ?,
                    coupon_discount_price = ?,
                    points_spent_amount = ?,
                    payment_amount = ?,
                    payment_method = ?,
                    payment_gateway_names = ?,
                    paid = ?,
                    canceled = ?,
                    cancel_date = ?,
                    first_order = ?,
                    CollectedDate = GETDATE()
                WHERE order_id = ?
            """, (
                data['order_date'], data['payment_date'], data['order_status'],
                data['shipping_status'], data['shipped_date'], data['purchaseconfirmation_date'],
                data['member_id'], data['billing_name'],
                data['member_email'], data['order_place_name'], data['order_from_mobile'],
                data['order_price_amount'], data['shipping_fee'], data['coupon_discount_price'],
                data['points_spent_amount'], data['payment_amount'], data['payment_method'],
                data['payment_gateway_names'], data['paid'], data['canceled'],
                data['cancel_date'], data['first_order'],
                order_id
            ))
            return "UPDATE", cafe24_order_id
        else:
            self.cursor.execute("""
                INSERT INTO FrogCafe24Orders (
                    order_id, order_date, payment_date, order_status,
                    shipping_status, shipped_date, purchaseconfirmation_date,
                    member_id, billing_name, member_email,
                    order_place_name, order_from_mobile,
                    order_price_amount, shipping_fee, coupon_discount_price,
                    points_spent_amount, payment_amount,
                    payment_method, payment_gateway_names,
                    paid, canceled, cancel_date, first_order,
                    CollectedDate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                order_id, data['order_date'], data['payment_date'], data['order_status'],
                data['shipping_status'], data['shipped_date'], data['purchaseconfirmation_date'],
                data['member_id'], data['billing_name'],
                data['member_email'], data['order_place_name'], data['order_from_mobile'],
                data['order_price_amount'], data['shipping_fee'], data['coupon_discount_price'],
                data['points_spent_amount'], data['payment_amount'],
                data['payment_method'], data['payment_gateway_names'],
                data['paid'], data['canceled'], data['cancel_date'], data['first_order']
            ))
            self.cursor.execute("SELECT @@IDENTITY")
            result = self.cursor.fetchone()
            cafe24_order_id = int(result[0]) if result and result[0] else None
            return "INSERT", cafe24_order_id

    def _merge_order_detail(self, order, item, cafe24_order_id):
        """FrogCafe24OrdersDetail 테이블 MERGE"""
        order_id = order.get("order_id")
        order_item_code = item.get("order_item_code")

        self.cursor.execute(
            "SELECT DetailID FROM FrogCafe24OrdersDetail WHERE order_item_code = ?",
            (order_item_code,)
        )
        existing = self.cursor.fetchone()

        data = self._extract_detail_data(order, item)

        if existing:
            self.cursor.execute("""
                UPDATE FrogCafe24OrdersDetail SET
                    Cafe24OrderID = ?,
                    order_id = ?,
                    item_no = ?,
                    ProductUniqueCode = ?,
                    ProductID = ?,
                    custom_product_code = ?,
                    custom_variant_code = ?,
                    product_name = ?,
                    option_value = ?,
                    quantity = ?,
                    product_price = ?,
                    payment_amount = ?,
                    coupon_discount_price = ?,
                    order_status = ?,
                    order_status_additional_info = ?,
                    shipping_code = ?,
                    shipping_company_name = ?,
                    tracking_no = ?,
                    product_bundle = ?,
                    supplier_id = ?,
                    made_in_code = ?,
                    CollectedDate = GETDATE()
                WHERE order_item_code = ?
            """, (
                cafe24_order_id, data['order_id'], data['item_no'],
                data['ProductUniqueCode'], data['ProductID'],
                data['custom_product_code'], data['custom_variant_code'],
                data['product_name'], data['option_value'],
                data['quantity'], data['product_price'],
                data['payment_amount'], data['coupon_discount_price'],
                data['order_status'], data['order_status_additional_info'],
                data['shipping_code'], data['shipping_company_name'],
                data['tracking_no'], data['product_bundle'],
                data['supplier_id'], data['made_in_code'],
                order_item_code
            ))
            return "UPDATE", data['ProductID'], data['ProductUniqueCode']
        else:
            self.cursor.execute("""
                INSERT INTO FrogCafe24OrdersDetail (
                    Cafe24OrderID, order_id, order_item_code, item_no,
                    ProductUniqueCode, ProductID,
                    custom_product_code, custom_variant_code,
                    product_name, option_value,
                    quantity, product_price, payment_amount, coupon_discount_price,
                    order_status, order_status_additional_info,
                    shipping_code, shipping_company_name, tracking_no,
                    product_bundle, supplier_id, made_in_code,
                    CollectedDate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                cafe24_order_id, data['order_id'], order_item_code, data['item_no'],
                data['ProductUniqueCode'], data['ProductID'],
                data['custom_product_code'], data['custom_variant_code'],
                data['product_name'], data['option_value'],
                data['quantity'], data['product_price'],
                data['payment_amount'], data['coupon_discount_price'],
                data['order_status'], data['order_status_additional_info'],
                data['shipping_code'], data['shipping_company_name'],
                data['tracking_no'], data['product_bundle'],
                data['supplier_id'], data['made_in_code']
            ))
            return "INSERT", data['ProductID'], data['ProductUniqueCode']

    def _get_product_id(self, unique_code):
        """Product 테이블에서 UniqueCode로 ProductID 조회"""
        if not unique_code:
            return None
        try:
            self.cursor.execute(
                "SELECT ProductID FROM Product WHERE UniqueCode = ?",
                (unique_code,)
            )
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"[WARNING] ProductID 조회 실패 (UniqueCode: {unique_code}): {e}")
            return None

    def _extract_order_data(self, order):
        """주문 마스터 데이터 추출"""
        actual_amount = order.get('actual_order_amount', {})

        shipped_date = None
        purchaseconfirmation_date = None
        order_status = None
        items = order.get('items', [])
        for item in items:
            if item.get('shipped_date') and not shipped_date:
                shipped_date = item.get('shipped_date')
            if item.get('purchaseconfirmation_date') and not purchaseconfirmation_date:
                purchaseconfirmation_date = item.get('purchaseconfirmation_date')
            if item.get('order_status') and not order_status:
                order_status = item.get('order_status')
            if shipped_date and purchaseconfirmation_date and order_status:
                break

        return {
            'order_date': self._parse_datetime(order.get('order_date')),
            'payment_date': self._parse_datetime(order.get('payment_date')),
            'order_status': order_status,
            'shipping_status': order.get('shipping_status'),
            'shipped_date': self._parse_datetime(shipped_date),
            'purchaseconfirmation_date': self._parse_datetime(purchaseconfirmation_date),
            'member_id': order.get('member_id'),
            'billing_name': order.get('billing_name'),
            'member_email': order.get('member_email'),
            'order_place_name': order.get('order_place_name'),
            'order_from_mobile': self._parse_boolean(order.get('order_from_mobile')),
            'order_price_amount': actual_amount.get('order_price_amount'),
            'shipping_fee': actual_amount.get('shipping_fee'),
            'coupon_discount_price': actual_amount.get('coupon_discount_price'),
            'points_spent_amount': actual_amount.get('points_spent_amount'),
            'payment_amount': order.get('payment_amount'),
            'payment_method': ','.join(order.get('payment_method', [])) if isinstance(order.get('payment_method'), list) else order.get('payment_method'),
            'payment_gateway_names': ','.join(order.get('payment_gateway_names', [])) if isinstance(order.get('payment_gateway_names'), list) else order.get('payment_gateway_names'),
            'paid': self._parse_boolean(order.get('paid')),
            'canceled': self._parse_boolean(order.get('canceled')),
            'cancel_date': self._parse_datetime(order.get('cancel_date')),
            'first_order': self._parse_boolean(order.get('first_order'))
        }

    def _parse_datetime(self, datetime_str):
        """Cafe24 날짜 형식을 SQL Server 호환 형식으로 변환"""
        if not datetime_str or datetime_str == '':
            return None
        try:
            from dateutil import parser
            dt = parser.isoparse(datetime_str)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return datetime_str if datetime_str else None

    def _parse_boolean(self, bool_str):
        """Cafe24 boolean ('T'/'F') → Python boolean"""
        if bool_str == 'T':
            return True
        elif bool_str == 'F':
            return False
        else:
            return None

    def _extract_detail_data(self, order, item):
        """주문 상세 데이터 추출 (ProductUniqueCode, ProductID 포함)"""
        option_value = item.get('option_value')
        if not option_value or option_value == '':
            product_unique_code = item.get('custom_product_code')
        else:
            product_unique_code = item.get('custom_variant_code')

        if product_unique_code:
            product_unique_code = product_unique_code.rstrip('.')

        product_id = self._get_product_id(product_unique_code)

        return {
            'order_id': order.get('order_id'),
            'item_no': item.get('item_no'),
            'ProductUniqueCode': product_unique_code,
            'ProductID': product_id,
            'custom_product_code': item.get('custom_product_code'),
            'custom_variant_code': item.get('custom_variant_code'),
            'product_name': item.get('product_name'),
            'option_value': option_value,
            'quantity': item.get('quantity'),
            'product_price': item.get('product_price'),
            'payment_amount': item.get('payment_amount'),
            'coupon_discount_price': item.get('coupon_discount_price'),
            'order_status': item.get('order_status'),
            'order_status_additional_info': item.get('order_status_additional_info'),
            'shipping_code': item.get('shipping_code'),
            'shipping_company_name': item.get('shipping_company_name'),
            'tracking_no': item.get('tracking_no'),
            'product_bundle': self._parse_boolean(item.get('product_bundle')),
            'supplier_id': item.get('supplier_id'),
            'made_in_code': item.get('made_in_code')
        }

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
