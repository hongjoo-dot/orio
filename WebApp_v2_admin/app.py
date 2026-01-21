"""
Orio ERP System v2 - Refactored
Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Routers
from routers import product, brand, channel, sales, bom, pages
from routers import auth, admin, system_config
from routers import revenue_plan, promotion, target_sales

app = FastAPI(
    title="Orio ERP System v2",
    version="2.0.0",
    description="리팩토링된 ERP 시스템 - Repository 패턴 적용"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base Directory
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

# Mount static files (생성되면)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include Page Routers (HTML)
app.include_router(pages.router)

# Include Auth & Admin Routers
app.include_router(auth.router)
app.include_router(admin.router)

# Include API Routers (JSON)
app.include_router(product.router)
app.include_router(product.productbox_router)  # ProductBox 독립 라우터
app.include_router(brand.router)
app.include_router(channel.router)
app.include_router(channel.channeldetail_router)  # ChannelDetail 독립 라우터
app.include_router(sales.router)
app.include_router(revenue_plan.router)
app.include_router(promotion.router)
app.include_router(target_sales.router)
app.include_router(bom.router)
app.include_router(system_config.router)




@app.get("/api/health")
async def health():
    """헬스 체크"""
    from core import test_connection

    db_connected, db_info = test_connection()

    return {
        "status": "healthy" if db_connected else "unhealthy",
        "version": "2.0.0",
        "database": {
            "connected": db_connected,
            "info": db_info if db_connected else "연결 실패"
        }
    }


if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("Orio ERP System v2.0 - Refactored with Repository Pattern")
    print("=" * 70)
    print("[OK] BaseRepository Pattern Applied")
    print("[OK] QueryBuilder for Dynamic Queries")
    print("[OK] Context Manager DB Connection")
    print("[OK] Authentication & Authorization (JWT)")
    print("[OK] Activity Logging")
    print("=" * 70)
    print("URL: http://localhost:8002")
    print("API Docs: http://localhost:8002/docs")
    print("=" * 70)

    uvicorn.run(app, host="0.0.0.0", port=8002)

