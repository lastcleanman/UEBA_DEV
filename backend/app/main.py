import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.core.logger import logger
from app.core.database import engine
from app.models.settings import Base
from app.core.ingestion.edge_hub import global_edge_hub
from app.modules.collectors.router import router as collectors_router

# ⭐️ 기본 필수 라우터 임포트
from app.api.v1.routes_modules import router as modules_router

# ⭐️ 추가: 라이선스 매니저 임포트
from app.license.manager import license_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("🚀 차세대 UEBA 백엔드 서버 기동을 시작합니다.")
    logger.info("=" * 50)

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 데이터베이스 테이블 연동 및 확인 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패 (DB 컨테이너가 켜져 있는지 확인하세요): {e}")

    # collectors start (try/except)
    try:
        await global_edge_hub.start_all()
    except Exception as e:
        logger.exception(f"❌ EdgeHub start_all failed (server will continue): {e}")

    yield

    logger.info("🛑 서버 종료 신호를 받았습니다. 안전하게 종료합니다.")
    try:
        await global_edge_hub.stop_all()
    except Exception as e:
        logger.exception(f"❌ EdgeHub stop_all failed: {e}")
    logger.info("✅ 모든 백그라운드 태스크 및 DB 연결이 해제되었습니다.")


app = FastAPI(
    title="UEBA API Gateway",
    description="Multi-layered UEBA Detection & Operation API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "message": "UEBA Backend is running smoothly!"}


# =====================================================================
# 1. 코어 및 필수 공통 기능 마운트
# =====================================================================
app.include_router(collectors_router, prefix="/api/v1/collectors")
app.include_router(modules_router)


# =====================================================================
# 2. 라이선스 기반 동적 모듈 마운트 (Plug-in Architecture)
# =====================================================================
active_modules = license_manager.get_active_modules()
logger.info(f"🔑 활성화된 라이선스 모듈: {active_modules}")

# 1. AI Schema 모듈
if "ai_schema" in active_modules:
    from app.modules.ai_schema.router import router as ai_schema_router
    app.include_router(ai_schema_router, prefix="/api/v1/ai-schema")
    logger.info("🔌 플러그인 장착: [AI Schema]")

# 2. Detection 모듈
if "detection" in active_modules or "ml_detect" in active_modules:
    from app.modules.detection.router import router as detection_router
    app.include_router(detection_router, prefix="/api/v1/detection")
    logger.info("🔌 플러그인 장착: [Detection]")

# 3. Scoring 모듈
if "scoring" in active_modules:
    from app.modules.scoring.router import router as scoring_router
    app.include_router(scoring_router, prefix="/api/v1/scoring")
    logger.info("🔌 플러그인 장착: [Scoring]")

# 4. SOAR 모듈 (workflow, soar_api, advanced_soar 등)
if any(m in active_modules for m in ["workflow", "soar_api", "advanced_soar"]):
    from app.modules.soar.router import router as soar_router
    app.include_router(soar_router, prefix="/api/v1/soar")
    logger.info("🔌 플러그인 장착: [SOAR]")

# 5. Pipeline 모듈
if "pipeline" in active_modules:
    from app.modules.pipeline.router import router as pipeline_router
    app.include_router(pipeline_router, prefix="/api/v1/pipeline")
    logger.info("🔌 플러그인 장착: [Pipeline]")

# =====================================================================

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)