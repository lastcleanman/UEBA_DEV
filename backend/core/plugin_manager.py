import importlib
from backend.core.utils import get_logger

logger = get_logger("PluginManager")

class PluginManager:
    def __init__(self, global_config):
        self.config = global_config
        # ueba_settings.json 의 system 블록에서 라이선스 등급 확인
        self.license_tier = global_config.get("system", {}).get("license_tier", "enterprise").lower()
        self.allowed_features = self._get_allowed_features(self.license_tier)

    def _get_allowed_features(self, tier):
        """등급별 허용 기능 매핑"""
        tiers = {
            "basic": ["rule_engine", "rule_abnormal_time"],
            "standard": ["rule_engine", "rule_abnormal_time", "ml_zscore", "peer_group"],
            "enterprise": ["rule_engine", "rule_abnormal_time", "ml_anomaly", "gre_auto_rule", "xai_explain"]
        }
        return tiers.get(tier, tiers["basic"])

    def load_plugins(self, step_name):
        """현재 라이선스에 허락된 플러그인 경로만 반환"""
        raw_plugins = self.config.get("pipeline", {}).get(step_name, [])
        active_plugins = []
        
        for path in raw_plugins:
            plugin_id = path.split('.')[-1]
            if step_name != "detection" or plugin_id in self.allowed_features:
                active_plugins.append(path)
                
        return active_plugins

    def execute_plugins(self, spark, df, step_name, source_name=None):
        """허락된 플러그인들을 순차적으로 실행"""
        plugins = self.load_plugins(step_name)
        for path in plugins:
            try:
                plugin = importlib.import_module(path)
                if hasattr(plugin, "execute"):
                    df = plugin.execute(spark, df, source_name, self.config)
            except Exception as e:
                logger.error(f"❌ [{step_name}] {path} 실행 실패: {e}")
        return df

    def log_active_status(self):
        """⭐️ 현재 라이선스 및 로드된 플러그인 현황을 예쁘게 출력"""
        logger.info("=" * 65)
        logger.info(f"💎 [License Status] Current Tier : [ {self.license_tier.upper()} ]")
        logger.info("-" * 65)
        logger.info("🔌 [Active Pipeline Plugins]")
        for step in ["input", "process", "detection", "output"]:
            plugins = self.load_plugins(step)
            plugin_names = [p.split('.')[-1] for p in plugins]
            logger.info(f"   ▶ {step.upper():<10} : {', '.join(plugin_names) if plugin_names else 'None'}")
        logger.info("=" * 65)