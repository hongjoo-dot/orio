"""
사방넷 풀필먼트 재고/입고 수집 파이프라인
Timer Trigger에서 호출
"""

import logging
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)


def run_inventory_pipeline(snapshot_time: str = 'AM') -> dict:
    """
    재고 + 입고 수집 파이프라인 실행

    Args:
        snapshot_time: 'AM' (11시) 또는 'PM' (18시)

    Returns:
        dict: 실행 결과 요약
    """
    from .config import get_fulfillment_config
    from .api_client import SabangnetFulfillmentClient
    from .upload_to_db import InventoryUploader

    result = {
        'snapshot_time': snapshot_time,
        'inventory': {'total': 0, 'inserted': 0, 'updated': 0},
        'locations': {'inserted': 0},
        'receiving_plans': {'total': 0},
        'receiving_works': {'total': 0},
        'errors': []
    }

    try:
        # 실제 아웃바운드 IP 확인 (디버깅용)
        try:
            import requests as _req
            my_ip = _req.get('https://api.ipify.org', timeout=5).text
            logger.info(f'[파이프라인] 아웃바운드 IP: {my_ip}')
        except Exception:
            logger.warning('[파이프라인] IP 확인 실패')

        # 설정 로드
        config = get_fulfillment_config()
        client = SabangnetFulfillmentClient(config)
        uploader = InventoryUploader()

        # Step 0: ERPCode 매핑 로드 + 사방넷 출고상품 전체 조회 → 매핑 구축
        uploader.load_product_mapping()

        logger.info('[파이프라인] 사방넷 출고상품 전체 조회')
        shipping_products = client.get_shipping_products()

        if not shipping_products:
            logger.warning("[파이프라인] 사방넷에서 출고상품을 가져올 수 없습니다.")
            result['errors'].append('출고상품 조회 실패')
            return result

        uploader.build_shipping_product_mapping(shipping_products)
        shipping_ids = uploader.get_shipping_product_ids()

        # 매핑 통계
        mapped = sum(1 for v in uploader.product_mapping.values() if v.get('ProductID'))
        unmapped = len(shipping_products) - mapped
        result['mapping'] = {'total': len(shipping_products), 'matched': mapped, 'unmatched': unmapped}
        logger.info(f"[파이프라인] 출고상품: {len(shipping_ids)}개 (매핑 성공: {mapped}, 실패: {unmapped})")

        snapshot_date = datetime.today().strftime('%Y-%m-%d')

        # ============================================================
        # 1. 재고 스냅샷 수집
        # ============================================================
        logger.info('Step 1: 재고 스냅샷 수집')
        try:
            stocks = client.get_stocks(shipping_ids)
            if stocks:
                inv_result = uploader.upload_inventory_snapshots(stocks, snapshot_date, snapshot_time)
                result['inventory'] = inv_result
        except Exception as e:
            logger.error(f"재고 스냅샷 실패: {e}", exc_info=True)
            result['errors'].append(f'재고 스냅샷: {str(e)}')

        # ============================================================
        # 2. 로케이션별 재고 수집
        # ============================================================
        logger.info('Step 2: 로케이션별 재고 수집')
        try:
            locations = client.get_stock_locations(shipping_ids)
            if locations:
                loc_result = uploader.upload_location_snapshots(locations, snapshot_date, snapshot_time)
                result['locations'] = loc_result
        except Exception as e:
            logger.error(f"로케이션 스냅샷 실패: {e}", exc_info=True)
            result['errors'].append(f'로케이션 스냅샷: {str(e)}')

        # ============================================================
        # 3. 입고예정 수집
        # ============================================================
        logger.info('Step 3: 입고예정 수집')
        try:
            plans = client.get_receiving_plans()
            if plans:
                plan_result = uploader.upload_receiving_plans(plans)
                result['receiving_plans'] = plan_result

                # 예정대비입고현황 업데이트 (완료 또는 검수중인 것만)
                for plan in plans:
                    status = plan.get('plan_status')
                    if status in [2, 3]:  # 검수중, 완료
                        plan_id = plan.get('receiving_plan_id')
                        try:
                            plan_detail = client.get_receiving_plan_result(plan_id)
                            if plan_detail:
                                uploader.update_receiving_quantities(plan_id, plan_detail)
                        except Exception as e:
                            logger.warning(f"예정대비입고 업데이트 실패 (plan_id={plan_id}): {e}")
        except Exception as e:
            logger.error(f"입고예정 수집 실패: {e}", exc_info=True)
            result['errors'].append(f'입고예정: {str(e)}')

        # ============================================================
        # 4. 입고작업내역 수집 (최근 30일)
        # ============================================================
        logger.info('Step 4: 입고작업내역 수집')
        try:
            end_dt = datetime.today().strftime('%Y%m%d')
            start_dt = (datetime.today() - timedelta(days=30)).strftime('%Y%m%d')
            works = client.get_receiving_works(start_dt, end_dt)
            if works:
                work_result = uploader.upload_receiving_works(works)
                result['receiving_works'] = work_result
        except Exception as e:
            logger.error(f"입고작업내역 수집 실패: {e}", exc_info=True)
            result['errors'].append(f'입고작업내역: {str(e)}')

        # ============================================================
        # 5. Slack 알림
        # ============================================================
        _send_slack_summary(result)

        logger.info(f"[파이프라인] 완료: {result}")
        return result

    except Exception as e:
        logger.error(f"[파이프라인] 전체 실패: {e}", exc_info=True)
        _send_slack_error(str(e))
        raise


def _send_slack_summary(result: dict):
    """수집 결과 Slack 알림"""
    try:
        from slack_notifier import send_slack_notification

        inv = result['inventory']
        loc = result['locations']
        plans = result['receiving_plans']
        works = result['receiving_works']
        errors = result['errors']

        mapping = result.get('mapping', {})
        has_unmapped = mapping.get('unmatched', 0) > 0
        icon = '✅' if not errors and not has_unmapped else '⚠️'
        message = f"{icon} *[풀필먼트] 재고/입고 수집 완료 ({result['snapshot_time']})*\n\n"

        # 매핑 통계
        if mapping:
            message += f"🔗 *상품 매핑*: {mapping.get('total', 0)}개 중 {mapping.get('matched', 0)}개 성공"
            if has_unmapped:
                message += f" (*{mapping['unmatched']}개 미매핑*)"
            message += "\n"

        message += f"📦 *재고 스냅샷*: {inv.get('total', 0)}건 (INSERT: {inv.get('inserted', 0)}, UPDATE: {inv.get('updated', 0)})\n"
        message += f"📍 *로케이션*: {loc.get('inserted', 0)}건\n"
        message += f"📋 *입고예정*: {plans.get('total', 0)}건\n"
        message += f"🔧 *입고작업*: {works.get('total', 0)}건\n"

        if errors:
            message += f"\n❌ *오류*: {len(errors)}건\n"
            for err in errors:
                message += f"   - {err}\n"

        send_slack_notification(message)
    except Exception as e:
        logger.warning(f"Slack 알림 실패: {e}")


def _send_slack_error(error_msg: str):
    """오류 Slack 알림"""
    try:
        from slack_notifier import send_slack_notification
        send_slack_notification(f"❌ *[풀필먼트] 수집 실패*\n\n```{error_msg}```")
    except:
        pass
