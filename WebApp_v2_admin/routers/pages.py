"""
Pages Router
- HTML 템플릿 렌더링
- 로그인 페이지 제외 모든 페이지 인증 필수
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
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


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, redirect = Depends(require_login_for_page)):
    """대시보드 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_page": "dashboard"
    })


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


@router.get("/targets", response_class=HTMLResponse)
async def targets_page(request: Request, redirect = Depends(require_login_for_page)):
    """목표 관리 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("targets.html", {
        "request": request,
        "active_page": "targets"
    })


@router.get("/promotions", response_class=HTMLResponse)
async def promotions_page(request: Request, redirect = Depends(require_login_for_page)):
    """행사 관리 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("promotions.html", {
        "request": request,
        "active_page": "promotions"
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

