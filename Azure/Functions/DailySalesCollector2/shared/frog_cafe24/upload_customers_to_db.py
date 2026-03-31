"""
Frog Cafe24 고객 데이터 → Azure SQL Database 업로드
MERGE 로직: member_id 기준 INSERT/UPDATE
"""
import os
import logging
import pyodbc


class CustomerDatabaseUploader:
    """고객 데이터 DB 업로더 (Frog Cafe24)"""

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
            raise Exception("DB 연결 정보가 환경변수에 없습니다.")

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

    def merge_customers(self, customers_data):
        """고객 데이터를 DB에 MERGE"""
        inserted = 0
        updated = 0

        for i, customer in enumerate(customers_data):
            try:
                result = self._merge_customer(customer)
                if result == "INSERT":
                    inserted += 1
                elif result == "UPDATE":
                    updated += 1

            except Exception as e:
                logging.error(f"[ERROR] 고객 처리 실패 (member_id: {customer.get('member_id')}): {e}", exc_info=True)
                continue

            if (i + 1) % 7000 == 0:
                self.connection.commit()

        self.connection.commit()

        result = {
            "inserted": inserted,
            "updated": updated,
            "total": inserted + updated
        }

        return result

    def _merge_customer(self, customer):
        """FrogCafe24Customers 테이블 MERGE"""
        member_id = customer.get("member_id")

        self.cursor.execute(
            "SELECT CustomerID FROM FrogCafe24Customers WHERE member_id = ?",
            (member_id,)
        )
        existing = self.cursor.fetchone()

        data = self._extract_customer_data(customer)

        if existing:
            self.cursor.execute("""
                UPDATE FrogCafe24Customers SET
                    shop_no = ?, group_no = ?,
                    phone = ?, cellphone = ?,
                    member_authentication = ?,
                    authentication_method = ?,
                    sms = ?, news_mail = ?,
                    gender = ?,
                    total_points = ?, available_points = ?, used_points = ?,
                    use_mobile_app = ?, fixed_group = ?,
                    last_login_date = ?, created_date = ?,
                    next_grade = NULL, total_purchase_amount = NULL, total_purchase_count = NULL,
                    required_purchase_amount = NULL, required_purchase_count = NULL,
                    CollectedDate = GETDATE()
                WHERE member_id = ?
            """, (
                data['shop_no'], data['group_no'],
                data['phone'], data['cellphone'],
                data['member_authentication'],
                data['authentication_method'],
                data['sms'], data['news_mail'],
                data['gender'],
                data['total_points'], data['available_points'], data['used_points'],
                data['use_mobile_app'], data['fixed_group'],
                data['last_login_date'], data['created_date'],
                member_id
            ))
            return "UPDATE"
        else:
            self.cursor.execute("""
                INSERT INTO FrogCafe24Customers (
                    member_id, shop_no, group_no,
                    phone, cellphone,
                    member_authentication, authentication_method,
                    sms, news_mail,
                    gender,
                    total_points, available_points, used_points,
                    use_mobile_app, fixed_group,
                    last_login_date, created_date,
                    next_grade, total_purchase_amount, total_purchase_count,
                    required_purchase_amount, required_purchase_count,
                    CollectedDate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, GETDATE())
            """, (
                member_id,
                data['shop_no'], data['group_no'],
                data['phone'], data['cellphone'],
                data['member_authentication'],
                data['authentication_method'],
                data['sms'], data['news_mail'],
                data['gender'],
                data['total_points'], data['available_points'], data['used_points'],
                data['use_mobile_app'], data['fixed_group'],
                data['last_login_date'], data['created_date']
            ))
            return "INSERT"

    def _extract_customer_data(self, customer):
        """고객 데이터 추출 및 변환"""
        return {
            'shop_no': customer.get('shop_no'),
            'group_no': customer.get('group_no'),
            'phone': customer.get('phone'),
            'cellphone': customer.get('cellphone'),
            'member_authentication': self._parse_boolean(customer.get('member_authentication')),
            'authentication_method': customer.get('authentication_method'),
            'sms': self._parse_boolean(customer.get('sms')),
            'news_mail': self._parse_boolean(customer.get('news_mail')),
            'gender': customer.get('gender'),
            'total_points': customer.get('total_points'),
            'available_points': customer.get('available_points'),
            'used_points': customer.get('used_points'),
            'use_mobile_app': self._parse_boolean(customer.get('use_mobile_app')),
            'fixed_group': self._parse_boolean(customer.get('fixed_group')),
            'last_login_date': self._parse_datetime(customer.get('last_login_date')),
            'created_date': self._parse_datetime(customer.get('created_date')),
        }

    def _parse_datetime(self, datetime_str):
        if not datetime_str or datetime_str == '':
            return None
        try:
            from dateutil import parser
            dt = parser.isoparse(datetime_str)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return datetime_str if datetime_str else None

    def _parse_boolean(self, bool_str):
        if bool_str == 'T':
            return True
        elif bool_str == 'F':
            return False
        else:
            return None

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
