import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

def setup_logger(app_name: str = "UEBA"):
    """
    날짜별로 로그 파일이 분리되는 전역 로거를 설정합니다.
    """
    # 로그 파일이 저장될 절대 경로 설정 (/backend/logs)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_dir = os.path.join(base_dir, "logs")
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 로거 객체 생성
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.INFO)

    # 이미 핸들러가 추가되어 있다면 중복 추가 방지
    if not logger.handlers:
        # 1. 파일 핸들러 (매일 자정에 새로운 파일 생성, 30일 보관)
        log_file_path = os.path.join(log_dir, "ueba_server.log")
        file_handler = TimedRotatingFileHandler(
            filename=log_file_path,
            when="midnight",       # 자정 기준 로테이션
            interval=1,            # 1일 단위
            backupCount=30,        # 최대 30일치 로그 보관
            encoding="utf-8"
        )
        # 파일명 확장자 설정 (예: ueba_server.log.2026-02-26)
        file_handler.suffix = "%Y-%m-%d.log"
        
        # 2. 콘솔 핸들러 (개발 시 화면에서 바로 볼 수 있도록)
        console_handler = logging.StreamHandler()

        # 로그 포맷 설정
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# 다른 파일에서 쉽게 import 할 수 있도록 미리 인스턴스화
logger = setup_logger()