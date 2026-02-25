import os

# 1. 프로젝트 경로 동적 계산
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CORE_DIR)

# 2. 주요 폴더(Directory) 경로 동적 맵핑 (모두 BACKEND_DIR 기준)
DATA_DIR = os.path.join(BACKEND_DIR, "data")
INPUT_DIR = os.path.join(DATA_DIR, "input")
LOG_DIR = os.path.join(DATA_DIR, "logs")
INTERMEDIATE_PATH = os.path.join(DATA_DIR, "intermediate")
CONF_DIR = os.path.join(BACKEND_DIR, "conf")

# 3. 주요 파일(File) 경로 동적 맵핑
# ⭐️ 파일명이 config.json이 아니라 ueba_settings.json 이었습니다!
CONFIG_FILE = os.path.join(CONF_DIR, "ueba_settings.json")
WATERMARK_FILE = os.path.join(CONF_DIR, "watermark.json")
MODE_FILE = os.path.join(DATA_DIR, "mode.txt")

# 4. 실행 스크립트 경로 동적 맵핑
SPARK_JOB_SCRIPT = os.path.join(CORE_DIR, "jobs", "spark_pipeline.py")
PARSER_DIR = os.path.join(DATA_DIR, "parsers")