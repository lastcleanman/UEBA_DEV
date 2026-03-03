# 1. Node.js 베이스 이미지 설정 (가벼운 alpine 버전 권장)
FROM node:20-alpine

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 패키지 설치를 위해 설정 파일 복사
COPY package*.json ./

# 4. 의존성 패키지 설치
RUN npm install

# 5. 소스 코드 전체 복사
COPY . .

# 6. 개발 서버 실행 (npm run dev)
# --host 0.0.0.0 옵션은 컨테이너 외부 접속을 위해 필요합니다.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]