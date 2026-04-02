"""
Pages Router
- HTML 템플릿 렌더링
- 로그인 페이지 제외 모든 페이지 인증 필수
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from core.dependencies import require_login_for_page

router = APIRouter(tags=["Pages"])

# Templates 디렉토리 설정
BASE_DIR = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """로그인 페이지"""
    return templates.TemplateResponse("login.html", {
        "request": request
    })


@router.get("/")
async def root():
    """루트 → 통합 조회로 리다이렉트"""
    return RedirectResponse(url="/expected-sales-integration", status_code=302)


@router.get("/products", response_class=HTMLResponse)
async def products_page(request: Request, redirect = Depends(require_login_for_page)):
    """제품 관리 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("products.html", {
        "request": request,
        "active_page": "products"
    })


@router.get("/sales", response_class=HTMLResponse)
async def sales_page(request: Request, redirect = Depends(require_login_for_page)):
    """판매 관리 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("sales.html", {
        "request": request,
        "active_page": "sales"
    })


@router.get("/channels", response_class=HTMLResponse)
async def channels_page(request: Request, redirect = Depends(require_login_for_page)):
    """채널 관리 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("channels.html", {
        "request": request,
        "active_page": "channels"
    })


@router.get("/bom", response_class=HTMLResponse)
async def bom_page(request: Request, redirect = Depends(require_login_for_page)):
    """BOM 관리 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("bom.html", {
        "request": request,
        "active_page": "bom"
    })


@router.get("/expected-3p", response_class=HTMLResponse)
async def expected_3p_page(request: Request, redirect = Depends(require_login_for_page)):
    """위탁 예상 매출 페이지 (정기/비정기 탭)"""
    if redirect:
        return redirect
    return templates.TemplateResponse("expected_3p_regular.html", {
        "request": request,
        "active_page": "expected-3p"
    })


@router.get("/expected-1p", response_class=HTMLResponse)
async def expected_1p_page(request: Request, redirect = Depends(require_login_for_page)):
    """사입 예상 매출 페이지 (정기/비정기 탭)"""
    if redirect:
        return redirect
    return templates.TemplateResponse("expected_1p_regular.html", {
        "request": request,
        "active_page": "expected-1p"
    })


@router.get("/expected-sales-integration", response_class=HTMLResponse)
async def expected_sales_integration_page(request: Request, redirect = Depends(require_login_for_page)):
    """예상 판매량 통합 조회 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("expected_sales_integration.html", {
        "request": request,
        "active_page": "expected-sales-integration"
    })


@router.get("/withdrawal-plans", response_class=HTMLResponse)
async def withdrawal_plans_page(request: Request, redirect = Depends(require_login_for_page)):
    """불출 계획 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("withdrawal_plan.html", {
        "request": request,
        "active_page": "withdrawal-plans"
    })


@router.get("/coupang/upload", response_class=HTMLResponse)
async def coupang_upload_page(request: Request, redirect = Depends(require_login_for_page)):
    """쿠팡 데이터 업로드 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("coupang_upload.html", {
        "request": request,
        "active_page": "coupang-upload"
    })


@router.get("/data-query", response_class=HTMLResponse)
async def data_query_page(request: Request, redirect = Depends(require_login_for_page)):
    """데이터 조회 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("data_query.html", {
        "request": request,
        "active_page": "data-query"
    })


@router.get("/sabangnet/inventory", response_class=HTMLResponse)
async def sabangnet_inventory_page(request: Request, redirect = Depends(require_login_for_page)):
    """WMS 재고 조회 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("sabangnet_inventory.html", {
        "request": request,
        "active_page": "sabangnet-inventory"
    })


@router.get("/sabangnet/inbound", response_class=HTMLResponse)
async def sabangnet_inbound_page(request: Request, redirect = Depends(require_login_for_page)):
    """WMS 입고 관리 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("sabangnet_inbound.html", {
        "request": request,
        "active_page": "sabangnet-inbound"
    })


@router.get("/utilities", response_class=HTMLResponse)
async def utilities_page(request: Request, redirect = Depends(require_login_for_page)):
    """유틸리티 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("utilities.html", {
        "request": request,
        "active_page": "utilities"
    })


# ========================
# Admin Pages (Admin only)
# ========================

@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request, redirect = Depends(require_login_for_page)):
    """사용자 관리 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "active_page": "admin-users"
    })


@router.get("/admin/activity-log", response_class=HTMLResponse)
async def activity_log_page(request: Request, redirect = Depends(require_login_for_page)):
    """활동 이력 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("activity_log.html", {
        "request": request,
        "active_page": "activity-log"
    })


@router.get("/admin/permissions", response_class=HTMLResponse)
async def permissions_page(request: Request, redirect = Depends(require_login_for_page)):
    """권한 관리 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("permissions.html", {
        "request": request,
        "active_page": "permissions"
    })


@router.get("/admin/system-config", response_class=HTMLResponse)
async def system_config_page(request: Request, redirect = Depends(require_login_for_page)):
    """시스템 설정 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("system_config.html", {
        "request": request,
        "active_page": "system-config"
    })

