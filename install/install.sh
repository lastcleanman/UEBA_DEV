#!/bin/bash
echo "📦 UEBA Solution Enterprise 설치를 시작합니다..."

# 1. 필수 디렉토리 생성
mkdir -p /opt/UEBA_DEV/{conf/parsers,data/logs,logs,core,plugins/detect,plugins/input,plugins/output,plugins/process,tools}

# 2. 소스 파일 복사 (현재 위치 기준)
cp -r ../* /opt/UEBA_DEV/

# 3. 도커 이미지 빌드 및 실행
cd /opt/UEBA_DEV
docker-compose up -d --build

echo "✅ 설치가 완료되었습니다. 'docker logs -f ueba-engine-dev'로 상태를 확인하세요."