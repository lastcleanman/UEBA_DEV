FROM apache/spark:3.4.1

USER root

# OS 필수 라이브러리 설치
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev && rm -rf /var/lib/apt/lists/*

# ⭐️ 끝에 pyspark 추가! (이제 python3 명령어로도 무조건 인식합니다)
RUN python3 -m pip install --no-cache-dir pandas sqlalchemy pymysql psycopg2-binary pyspark

# 컨테이너 내부 작업 디렉토리
WORKDIR /UEBA_DEV