#!/bin/bash
echo "🚀 Starting UEBA Engine..."

# 이미 실행 중인지 확인
if [ -f "/tmp/ueba_engine.pid" ]; then
    echo "⚠️ UEBA Engine is already running. (PID: $(cat /tmp/ueba_engine.pid))"
    exit 1
fi

# Docker 컨테이너 내부에서 백그라운드로 엔진(orchestrator.py) 실행
docker exec -d ueba-spark bash -c "nohup python3 /UEBA/core/engine.py > /UEBA/logs/engine.log 2>&1 & echo \$! > /UEBA/engine.pid"

# 호스트에도 PID 파일 복사하여 상태 관리
docker cp ueba-spark:/UEBA/engine.pid /tmp/ueba_engine.pid
echo "✅ UEBA Engine started successfully in background."