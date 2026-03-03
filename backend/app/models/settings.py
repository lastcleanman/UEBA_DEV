import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()

# 라이선스 등급 Enum
class LicenseTier(str, enum.Enum):
    BASIC = "basic"
    STANDARD = "standard"
    ENTERPRISE = "enterprise"

# 수집 타겟 프로토콜 Enum
class TargetType(str, enum.Enum):
    JDBC = "jdbc"
    SSH = "ssh"
    WMI = "wmi"
    API = "api"

# ---------------------------------------------------------
# 1. 시스템 및 라이선스 설정 테이블 (관리자 UI 제어용)
# ---------------------------------------------------------
class UEBASystemSetting(Base):
    __tablename__ = "ueba_system_settings"

    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String, nullable=True)
    tier = Column(Enum(LicenseTier), default=LicenseTier.BASIC, nullable=False)
    
    # --- 모듈 활성화 토글 (UI에서 ON/OFF 제어) ---
    # [Tier 1] Basic
    mod_onboarding = Column(Boolean, default=True)
    mod_detect = Column(Boolean, default=True)
    mod_scoring = Column(Boolean, default=True)
    mod_workflow = Column(Boolean, default=True)
    
    # [Tier 2] Standard
    mod_ai_schema = Column(Boolean, default=False)
    mod_ml_detect = Column(Boolean, default=False)
    mod_explainer = Column(Boolean, default=False)
    mod_soar_api = Column(Boolean, default=False)
    
    # [Tier 3] Enterprise
    mod_gre_pipeline = Column(Boolean, default=False)
    mod_advanced_soar = Column(Boolean, default=False)
    mod_distribute = Column(Boolean, default=False)
    mod_deploy_signed = Column(Boolean, default=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------
# 2. 다중 원격 수집 타겟 테이블 (Remote Fetch)
# ---------------------------------------------------------
class CollectorTarget(Base):
    __tablename__ = "collector_targets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_name = Column(String, unique=True, index=True, nullable=False) # 예: "legacy-db-01"
    target_type = Column(Enum(TargetType), nullable=False)                 # jdbc, ssh 등
    host = Column(String, nullable=False)                                  # IP 또는 도메인
    port = Column(Integer, nullable=False)
    
    # 핵심! JDBC 드라이버, SSH 경로 등 프로토콜마다 다른 설정값을 유연하게 저장
    # 예: {"driver": "org.mariadb.jdbc.Driver", "db_name": "hr_db"} 
    # 예: {"log_path": "/var/log/secure", "ssh_user": "root"}
    connection_info = Column(JSONB, nullable=False, default={})            
    
    interval_sec = Column(Integer, default=300)                            # 수집 주기 (초)
    is_active = Column(Boolean, default=True)                              # UI에서 수집 일시정지 기능

    last_run_at = Column(DateTime, nullable=True)                          # 마지막 수집 시간 추적
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)