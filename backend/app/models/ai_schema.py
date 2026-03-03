from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
from app.models.settings import Base

class AISchemaHistory(Base):
    __tablename__ = "ai_schema_history"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True)
    log_type = Column(String)                 # 예: syslog, event 등
    accuracy = Column(Float)                  # AI 학습 스키마 매칭 정확도 (%)
    processed_count = Column(Integer)         # 학습에 사용된 로그 건수
    xml_file_path = Column(String)            # 생성된 XML 파일의 물리적 경로
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))