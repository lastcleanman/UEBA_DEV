# 1. OS 버전
FROM python:3.10-slim-bookworm

# 2. 필수 시스템 패키지 설치 (PySpark용 Java 및 프로세스 관리 도구)
# 설치 완료 후 찌꺼기를 지워 이미지 용량을 최적화합니다.
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jre-headless procps curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 3. 환경 변수 세팅
# Java 11은 메모리 보안 이슈가 없으므로 지저분한 JDK_JAVA_OPTIONS가 필요 없습니다!
ENV PYTHONPATH=/UEBA_DEV

# 4. 작업 디렉토리 설정
WORKDIR /UEBA_DEV/backend

# 5. 파이썬 패키지 복사 및 설치
# 도커 캐시 기능을 활용하기 위해 소스 코드보다 먼저 복사합니다.
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. 컨테이너 유지 명령어 (현재의 개발/테스트 환경 유지용)
# 향후 Phase 2에서 uvicorn(API 서버) 실행 명령어로 교체될 예정입니다.
CMD ["tail", "-f", "/dev/null"]