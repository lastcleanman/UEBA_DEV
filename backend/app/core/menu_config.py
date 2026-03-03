"""
프론트엔드 좌측 메뉴 및 시스템 파이프라인 구조 설정 파일입니다.
새로운 메뉴를 추가하거나 이름을 변경할 때 이 파일만 수정하세요.
"""

PIPELINE_MENU_CONFIG = [
    {
        "key": "ingestion",
        "label": "1. 수집 및 정제 (Ingestion)",
        "items": [
            {"id": "ai_schema", "label": "AI 스키마 자동추론", "to": "/pipeline/schema"},
            {"id": "parser", "label": "파서 빌더 (수동)", "to": "/pipeline/parser"},
            {"id": "viewer", "label": "스키마 관리 및 배포", "to": "/pipeline/viewer"},
        ]
    },
    {
        "key": "detection",
        "label": "2. 분석 및 탐지 (Detection)",
        "items": [
            {"id": "detect", "label": "임계치/룰 기반 탐지", "to": "/analysis/detect"},
            {"id": "ml_detect", "label": "ML 이상 행위 탐지", "to": "/analysis/ml-detect"},
            {"id": "scoring", "label": "자산 위험도 스코어링", "to": "/analysis/scoring"},
        ]
    },
    {
        "key": "response",
        "label": "3. 자동화 대응 (SOAR)",
        "items": [
            {"id": "workflow", "label": "대응 워크플로우", "to": "/response/workflow"},
            {"id": "soar_api", "label": "SOAR API 연동", "to": "/response/soar"},
            {"id": "advanced_soar", "label": "고급 플레이북", "to": "/response/advanced"},
        ]
    },
    {
        "key": "settings",
        "label": "⚙️ 시스템 공통 설정",
        "items": [
            {"id": "grep_pipeline", "label": "Grep 파이프라인 설정", "to": "/settings/grep"},
            {"id": "deploy", "label": "에이전트 배포 관리", "to": "/settings/deploy"},
        ]
    }
]