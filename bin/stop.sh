#!/bin/bash
echo "🛑 Stopping UEBA Engine..."

if [ ! -f "/tmp/ueba_engine.pid" ]; then
    echo "⚠️ UEBA Engine is not running."
    exit 1
fi

PID=$(cat /tmp/ueba_engine.pid)
# 컨테이너 내부의 프로세스 종료 (SIGTERM)
docker exec ueba-spark kill -15 $PID

rm -f /tmp/ueba_engine.pid
echo "✅ UEBA Engine stopped safely."