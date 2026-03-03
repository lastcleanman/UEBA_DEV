import logging
from typing import List

logger = logging.getLogger("LicenseManager")

class LicenseManager:
    """
    고객사의 라이선스 등급(Basic, Standard, Enterprise)에 따라 
    사용 가능한 기능(Module)을 제어합니다.
    """
    def __init__(self, current_tier: str = "standard"):
        # 실제 환경에서는 license.yaml 파일이나 DB에서 읽어옵니다.
        self.current_tier = current_tier.lower()
        
        # 라이선스 등급별 허용된 기능(모듈) 목록
        # 프론트엔드 모듈 ID(하이픈 포함)와 백엔드 폴더명(언더바) 모두 호환되도록 구성
        self._tier_permissions = {
            "basic": ["parser", "viewer", "detect", "scoring", "workflow"],
            "standard": [
                "parser", "viewer", "ai_schema", "detect", "ml_detect", "scoring", "workflow", "soar_api"
            ],
            "enterprise": [
                "parser", "viewer", "ai_schema", "detect", "ml_detect", "scoring", "workflow", "soar_api",
                "advanced_soar", "deploy", "grep_pipeline"
            ]
        }

    def get_tenant_license(self, tenant_id: str) -> str:
        """특정 테넌트(고객사)의 라이선스 등급을 반환합니다."""
        return self.current_tier

    def get_active_modules(self) -> List[str]:
        """현재 라이선스에서 활성화할 수 있는 모듈 이름을 반환합니다."""
        return self._tier_permissions.get(self.current_tier, [])

    def is_module_allowed(self, module_name: str) -> bool:
        """특정 모듈이 현재 라이선스에서 허용되는지 확인합니다. (백엔드 라우터 마운트용)"""
        return module_name in self.get_active_modules()

    # ⭐️ 프론트엔드 메뉴 UI(routes_modules.py) 호환성을 위한 함수 추가!
    def is_enabled(self, tenant_id: str, module_id: str) -> bool:
        """특정 테넌트가 해당 모듈(프론트엔드 ID 기준)을 사용할 권한이 있는지 확인합니다."""
        tier = self.get_tenant_license(tenant_id)
        allowed_modules = self._tier_permissions.get(tier, [])
        return module_id in allowed_modules

# 전역에서 사용할 싱글톤 인스턴스
license_manager = LicenseManager(current_tier="standard")