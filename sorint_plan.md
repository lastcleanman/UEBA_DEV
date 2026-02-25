# 백서 정합성 2주 스프린트 리팩토링 계획 (파일 단위 + 코드 베이스라인)

## 목표
- 백서의 핵심 축(다층 탐지, HIL 대응, GRE, 운영 내구성)을 현재 코드 구조에 단계적으로 반영한다.
- 이번 스프린트에서는 **동작 가능한 스캐폴딩 코드 + 라우팅 + 확장 지점**을 우선 구축한다.

## 산출물(이번 커밋에 포함)
- 신규 도메인 패키지
  - `backend/core/detection/*`
  - `backend/core/response/*`
  - `backend/core/intelligence/gre/*`
  - `backend/core/platform/*`
- 신규 API 샘플 라우터
  - `backend/core/api/routers/roadmap.py`
- 메인 라우터 등록
  - `backend/main.py`
- 설정 보완
  - `backend/core/config.py` (`PARSER_DIR` 추가)
- 의존성 보완
  - `backend/requirements.txt` (`requests` 추가)

---

## Week 1 (아키텍처 정렬 & 도메인 분리)

### 1) Detection 도메인 분리
- 파일:
  - `backend/core/detection/scoring.py`
  - `backend/core/detection/statistical/zscore.py`
  - `backend/core/detection/sequence/chain_detector.py`
  - `backend/core/detection/xai/explainer.py`
- 작업:
  - Unified Risk Score 선형 결합기 추가
  - Z-Score 및 정규화 유틸 추가
  - 시퀀스 체인(킬체인 유사) 탐지 스캐폴딩 추가
  - XAI 자연어 설명 스캐폴딩 추가

### 2) Response/HIL 도메인 분리
- 파일:
  - `backend/core/response/models.py`
  - `backend/core/response/webhook_client.py`
  - `backend/core/response/hil/service.py`
  - `backend/core/response/watchlist/service.py`
- 작업:
  - 대응 액션 모델 도입
  - 표준 Webhook 전송 유틸 추가
  - 소명(HIL) 메시지 생성 서비스 추가
  - Watchlist 가중치 계산 서비스 추가

### 3) Platform(State) 기초 계층 도입
- 파일:
  - `backend/core/platform/state_store.py`
- 작업:
  - PipelineStateStore 인터페이스와 InMemory 구현체 제공
  - 이후 Redis/Postgres 상태 저장소로 치환 가능한 지점 확보

---

## Week 2 (Intelligence/GRE + API 연결 + 운영성)

### 4) GRE 후보 생성 도메인 추가
- 파일:
  - `backend/core/intelligence/gre/service.py`
- 작업:
  - 신호 기반 후보 룰 생성 스캐폴딩 도입
  - 향후 Rule Mining/LLM 생성 단계의 입력 인터페이스 고정

### 5) 도메인 API 노출 (검증용)
- 파일:
  - `backend/core/api/routers/roadmap.py`
  - `backend/main.py`
- 작업:
  - `/api/v1/roadmap/capabilities` 엔드포인트 추가
  - 점수 집계/시퀀스/XAI/GRE 샘플 결과를 단일 API로 확인 가능

### 6) 설정/정합성 보완
- 파일:
  - `backend/core/config.py`
  - `backend/requirements.txt`
- 작업:
  - 파서 경로 상수 `PARSER_DIR` 추가
  - Webhook 연동용 `requests` 의존성 명시

---

## 다음 단계(후속 스프린트 권장)
1. `pipeline.py`의 in-memory 상태를 `PipelineStateStore`로 치환.
2. `/api/*`와 `/api/v1/*` 엔드포인트 버전 체계 단일화.
3. GRE 후보를 실제 룰 파일/DB에 저장하는 라이프사이클 구현.
4. XAI를 SHAP 기반으로 교체하고 대시보드 카드로 연동.
5. HIL 소명 결과를 DB 이력(Audit Trail)로 영구화.

---

## 검증 방법
- `python -m compileall backend`
- (선택) `curl http://localhost:8000/api/v1/roadmap/capabilities`