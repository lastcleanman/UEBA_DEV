import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

logger = logging.getLogger("UEBA")

# PostgreSQL 연결 정보 (docker-compose.yml 기준)
SQLALCHEMY_DATABASE_URL = "postgresql://admin:Suju!0901@postgres:5432/ueba_db"


# SQLAlchemy 엔진 생성
try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True # 연결이 끊어졌는지 미리 확인
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("✅ 데이터베이스 엔진 초기화 완료")
except Exception as e:
    logger.error(f"❌ 데이터베이스 엔진 초기화 실패: {e}")

# API 라우터에서 DB 세션을 주입(Dependency)받기 위한 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()