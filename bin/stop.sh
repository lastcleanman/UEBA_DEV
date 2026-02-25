#!/bin/bash

echo "🛑 UEBA Backend & Engine 서비스를 종료합니다..."

# 1. FastAPI (uvicorn) 프로세스 종료
pkill -f "uvicorn main:app"
if [ $? -eq 0 ]; then
    echo "⏹️ FastAPI 서버가 종료되었습니다."
else
    echo "⚠️ 실행 중인 FastAPI 서버를 찾을 수 없습니다."
fi

# 2. Core Engine 프로세스 종료
pkill -f "python3 core/engine.py"
if [ $? -eq 0 ]; then
    echo "⏹️ UEBA Core Engine이 종료되었습니다."
else
    echo "⚠️ 실행 중인 Core Engine을 찾을 수 없습니다."
fi

echo "✅ 모든 서비스가 안전하게 종료되었습니다."