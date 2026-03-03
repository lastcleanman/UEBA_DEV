# 1. 베이스 이미지 설정
FROM python:3.12-slim

# 2. 작업 디렉토리 설정 (컨테이너 내부 경로)
WORKDIR /app

# 3. 필요한 패키지 설치를 위해 requirements.txt 복사
# (파일이 없다면 이 줄은 주석 처리해도 되지만, 보통 만들어두는 게 좋습니다)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || echo "No requirements.txt found"

# 4. 소스 코드 전체 복사
COPY . .

# 5. 실행 명령어 (모듈 방식으로 실행)
CMD ["python3", "-m", "app.main"]