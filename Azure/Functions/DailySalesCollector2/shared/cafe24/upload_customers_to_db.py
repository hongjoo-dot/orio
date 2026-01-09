"""
Cafe24 고객 데이터 → Azure SQL Database 업로드
MERGE 로직: member_id 기준 INSERT/UPDATE
"""
import os
import logging
import pyodbc


class CustomerDatabaseUploader:
    """고객 데이터 DB 업로더"""

    def __init__(self):
        """환경변수에서 DB 연결 정보 로드"""
        connection_string = self._get_connection_string()
        self.connection = pyodbc.connect(connection_string)
        self.cursor = self.connection.cursor()

    def _get_connection_string(self):
        """환경변수에서 연결 문자열 생성"""
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
        """
        고객 데이터를 DB에 MERGE

        Args:
            customers_data: 고객 데이터 리스트

        Returns:
            dict: 결과 통계
        """
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

            # 배치 커밋 (7000건마다)
            if (i + 1) % 7000 == 0:
                self.connection.commit()

        # Commit
        self.connection.commit()

        result = {
            "inserted": inserted,
            "updated": updated,
            "total": inserted + updated
        }



        return result

    def _merge_customer(self, customer):
        """
        Cafe24Customers 테이블 MERGE

        Returns:
            str: "INSERT" or "UPDATE"
        """
        member_id = customer.get("member_id")

        # 기존 데이터 확인
        self.cursor.execute(
            "SELECT CustomerID FROM Cafe24Customers WHERE member_id = ?",
            (member_id,)
        )
        existing = self.cursor.fetchone()

        # 공통 데이터 추출
        data = self._extract_customer_data(customer)

        if existing:
            # UPDATE (/admin/customersprivacy API 필드 + purchase 필드는 NULL)
            self.cursor.execute("""
                UPDATE Cafe24Customers SET
                    shop_no = ?, group_no = ?,
                    member_authentication = ?, use_blacklist = ?, blacklist_type = ?,
                    authentication_method = ?,
                    sms = ?, news_mail = ?,
                    gender = ?, solar_calendar = ?,
                    total_points = ?, available_points = ?, used_points = ?, available_credits = ?,
                    use_mobile_app = ?, fixed_group = ?,
                    last_login_date = ?, created_date = ?,
                    next_grade = NULL, total_purchase_amount = NULL, total_purchase_count = NULL,
                    required_purchase_amount = NULL, required_purchase_count = NULL,
                    CollectedDate = GETDATE()
                WHERE member_id = ?
            """, (
                data['shop_no'], data['group_no'],
                data['member_authentication'], data['use_blacklist'], data['blacklist_type'],
                data['authentication_method'],
                data['sms'], data['news_mail'],
                data['gender'], data['solar_calendar'],
                data['total_points'], data['available_points'], data['used_points'], data['available_credits'],
                data['use_mobile_app'], data['fixed_group'],
                data['last_login_date'], data['created_date'],
                member_id
            ))
            return "UPDATE"
        else:
            # INSERT (/admin/customersprivacy API 필드 + purchase 필드는 NULL)
            self.cursor.execute("""
                INSERT INTO Cafe24Customers (
                    member_id, shop_no, group_no,
                    member_authentication, use_blacklist, blacklist_type, authentication_method,
                    sms, news_mail,
                    gender, solar_calendar,
                    total_points, available_points, used_points, available_credits,
                    use_mobile_app, fixed_group,
                    last_login_date, created_date,
                    next_grade, total_purchase_amount, total_purchase_count,
                    required_purchase_amount, required_purchase_count,
                    CollectedDate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, GETDATE())
            """, (
                member_id,
                data['shop_no'], data['group_no'],
                data['member_authentication'], data['use_blacklist'], data['blacklist_type'],
                data['authentication_method'],
                data['sms'], data['news_mail'],
                data['gender'], data['solar_calendar'],
                data['total_points'], data['available_points'], data['used_points'], data['available_credits'],
                data['use_mobile_app'], data['fixed_group'],
                data['last_login_date'], data['created_date']
            ))
            return "INSERT"

    def _extract_customer_data(self, customer):
        """고객 데이터 추출 및 변환 (모든 필드 매핑)"""
        return {
            # 기본 정보
            'shop_no': customer.get('shop_no'),
            'group_no': customer.get('group_no'),
            'name': customer.get('name'),
            'name_english': customer.get('name_english'),
            'name_phonetic': customer.get('name_phonetic'),
            'phone': customer.get('phone'),
            'cellphone': customer.get('cellphone'),
            'email': customer.get('email'),
            'nick_name': customer.get('nick_name'),

            # 인증 및 보안
            'member_authentication': self._parse_boolean(customer.get('member_authentication')),
            'use_blacklist': self._parse_boolean(customer.get('use_blacklist')),
            'blacklist_type': customer.get('blacklist_type'),
            'authentication_method': customer.get('authentication_method'),
            'member_authority': customer.get('member_authority'),

            # 마케팅 동의
            'sms': self._parse_boolean(customer.get('sms')),
            'news_mail': self._parse_boolean(customer.get('news_mail')),
            'thirdparty_agree': self._parse_boolean(customer.get('thirdparty_agree')),

            # 개인 정보
            'gender': customer.get('gender'),
            'birthday': customer.get('birthday'),
            'solar_calendar': self._parse_boolean(customer.get('solar_calendar')),
            'wedding_anniversary': customer.get('wedding_anniversary'),
            'residence': customer.get('residence'),
            'interest': customer.get('interest'),
            'job_class': customer.get('job_class'),
            'job': customer.get('job'),

            # 주소
            'city': customer.get('city'),
            'state': customer.get('state'),
            'zipcode': customer.get('zipcode'),
            'address1': customer.get('address1'),
            'address2': customer.get('address2'),
            'country_code': customer.get('country_code'),

            # 포인트 및 크레딧
            'total_points': customer.get('total_points'),
            'available_points': customer.get('available_points'),
            'used_points': customer.get('used_points'),
            'available_credits': customer.get('available_credits'),

            # 회원 유형 및 상태
            'member_type': customer.get('member_type'),
            'use_mobile_app': self._parse_boolean(customer.get('use_mobile_app')),
            'join_path': customer.get('join_path'),
            'fixed_group': self._parse_boolean(customer.get('fixed_group')),
            'lifetime_member': self._parse_boolean(customer.get('lifetime_member')),

            # 날짜 정보
            'last_login_date': self._parse_datetime(customer.get('last_login_date')),
            'created_date': self._parse_datetime(customer.get('created_date')),
            'account_reactivation_date': self._parse_datetime(customer.get('account_reactivation_date')),

            # 등급 및 구매
            'next_grade': customer.get('next_grade'),
            'total_purchase_amount': customer.get('total_purchase_amount'),
            'total_purchase_count': customer.get('total_purchase_count'),
            'required_purchase_amount': customer.get('required_purchase_amount'),
            'required_purchase_count': customer.get('required_purchase_count'),

            # 법인/외국인 정보
            'company_type': customer.get('company_type'),
            'foreigner_type': customer.get('foreigner_type'),
            'corporate_name': customer.get('corporate_name'),
            'nationality': customer.get('nationality'),
            'shop_name': customer.get('shop_name'),
            'company_condition': customer.get('company_condition'),
            'company_line': customer.get('company_line'),

            # 환불 계좌
            'refund_bank_code': customer.get('refund_bank_code'),
            'refund_bank_account_no': customer.get('refund_bank_account_no'),
            'refund_bank_account_holder': customer.get('refund_bank_account_holder'),

            # 추천인
            'recommend_id': customer.get('recommend_id')
        }

    def _parse_datetime(self, datetime_str):
        """Cafe24 날짜 형식을 SQL Server 형식으로 변환"""
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

    def close(self):
        """연결 종료"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
