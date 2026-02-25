#!/bin/bash

echo "🚀 UEBA Backend & Engine 서비스를 시작합니다..."

# 1. 파이썬이 backend 폴더 내부(core, plugins 등)를 찾을 수 있도록 경로 강제 설정
export PYTHONPATH=/UEBA_DEV

# 2. 실행 디렉토리 이동
cd /UEBA_DEV/backend

# 3. 로그 폴더가 없으면 생성 (스크린샷 기준 data/logs)
mkdir -p /UEBA_DEV/backend/data/logs

# ==========================================
# 🟢 FastAPI 백엔드 서버 기동
# ==========================================
echo "▶️ [1/2] FastAPI 서버를 백그라운드에서 기동합니다. (Port: 8000)"
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /UEBA_DEV/backend/data/logs/api_nohup.log 2>&1 &

# ==========================================
# 🔵 UEBA Core Engine 기동
# ==========================================
echo "▶️ [2/2] UEBA Core Engine을 백그라운드에서 기동합니다."
nohup python3 core/engine.py > /UEBA_DEV/backend/data/logs/engine_nohup.log 2>&1 &

echo "✅ 모든 서비스가 성공적으로 실행되었습니다!"
echo "👉 실시간 API 로그 확인 : tail -f /UEBA_DEV/backend/data/logs/api_nohup.log"
echo "👉 실시간 엔진 로그 확인 : tail -f /UEBA_DEV/backend/data/logs/engine_nohup.log"