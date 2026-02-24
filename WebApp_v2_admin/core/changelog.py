"""
ChangeLog - 데이터 변경 이력 추적

필드 단위로 변경 전/후 값을 [dbo].[ChangeLog] 테이블에 기록합니다.
ActivityLog(행위 로그)와는 독립적으로 운영됩니다.
"""

from typing import Dict, Any, Optional, List


def _clean_table_name(table_name: str) -> str:
    """[dbo].[Product] → Product"""
    return table_name.split('.')[-1].strip('[]')


def _normalize_value(val) -> Optional[str]:
    """값을 비교/저장용 문자열로 정규화."""
    if val is None:
        return None
    s = str(val).strip()
    if s == '':
        return None
    # 숫자 정규화: 500.0 → 500, 0.0 → 0
    try:
        num = float(s)
        if num == int(num):
            return str(int(num))
        return s
    except (ValueError, TypeError):
        return s


def log_changes(
    cursor,
    table_name: str,
    record_id: Any,
    old_data: Optional[Dict[str, Any]],
    new_data: Dict[str, Any],
    user_id: int
) -> int:
    """
    필드별 변경 이력을 ChangeLog 테이블에 기록합니다.

    Args:
        cursor: DB cursor (이미 트랜잭션 내에 있어야 함)
        table_name: 대상 테이블명 (예: "[dbo].[Product]" 또는 "Product")
        record_id: 대상 레코드의 PK 값
        old_data: 변경 전 값 dict (INSERT 시 None)
        new_data: 변경 후 값 dict
        user_id: 변경한 사용자 ID

    Returns:
        int: 기록된 변경 건수
    """
    clean_name = _clean_table_name(table_name)
    record_id_str = str(record_id)
    logged = 0

    if old_data is None:
        # INSERT: 모든 new 값 기록
        for field, new_val in new_data.items():
            new_norm = _normalize_value(new_val)
            if new_norm is not None:
                cursor.execute(
                    """
                    INSERT INTO [dbo].[ChangeLog]
                        (TableName, RecordID, FieldName, OldValue, NewValue, ChangedBy)
                    VALUES (?, ?, ?, NULL, ?, ?)
                    """,
                    clean_name, record_id_str, field, new_norm, user_id
                )
                logged += 1
    else:
        # UPDATE: 변경된 필드만 기록
        for field in new_data:
            old_val = old_data.get(field)
            new_val = new_data[field]

            old_norm = _normalize_value(old_val)
            new_norm = _normalize_value(new_val)

            if old_norm != new_norm:
                cursor.execute(
                    """
                    INSERT INTO [dbo].[ChangeLog]
                        (TableName, RecordID, FieldName, OldValue, NewValue, ChangedBy)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    clean_name, record_id_str, field, old_norm, new_norm, user_id
                )
                logged += 1

    return logged


def log_changes_bulk(
    cursor,
    table_name: str,
    id_column: str,
    records: List[Dict[str, Any]],
    track_fields: List[str],
    user_id: int
) -> int:
    """
    bulk_update용 헬퍼. 변경 전 값을 일괄 조회 후 비교하여 기록합니다.

    Args:
        cursor: DB cursor
        table_name: 대상 테이블명
        id_column: PK 컬럼명 (예: "PlanID")
        records: 변경할 레코드 리스트 [{id_column: ..., field: ...}, ...]
        track_fields: 추적할 필드 목록 (예: ["PlannedQty", "Notes"])
        user_id: 변경한 사용자 ID

    Returns:
        int: 기록된 변경 건수
    """
    if not records:
        return 0

    # 1) 변경 전 값 일괄 조회
    record_ids = [r[id_column] for r in records if r.get(id_column)]
    if not record_ids:
        return 0

    columns_sql = ', '.join([id_column] + track_fields)
    clean_name = _clean_table_name(table_name)

    placeholders = ','.join(['?' for _ in record_ids])
    cursor.execute(
        f"SELECT {columns_sql} FROM [dbo].[{clean_name}] WHERE {id_column} IN ({placeholders})",
        *record_ids
    )

    # {record_id: {field: value}} 맵 생성
    old_data_map = {}
    for row in cursor.fetchall():
        rid = row[0]
        old_data_map[rid] = {track_fields[i]: row[i + 1] for i in range(len(track_fields))}

    # 2) 각 레코드별 변경 이력 기록
    total_logged = 0
    for record in records:
        rid = record.get(id_column)
        if not rid:
            continue

        old_data = old_data_map.get(rid)
        new_data = {f: record.get(f) for f in track_fields}

        if old_data is None:
            # 존재하지 않는 레코드 (INSERT로 간주)
            total_logged += log_changes(cursor, table_name, rid, None, new_data, user_id)
        else:
            total_logged += log_changes(cursor, table_name, rid, old_data, new_data, user_id)

    return total_logged
