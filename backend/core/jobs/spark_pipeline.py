import sys
import os
import json

# ⭐️ 1. 현재 파일(jobs) 위치를 기준으로 ROOT를 찾아 sys.path에 자동 주입
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ⭐️ 2. config.py에서 설정 경로를 깔끔하게 가져옴
from backend.core.config import CONFIG_FILE
from backend.core.utils import get_logger
from backend.core.plugin_manager import PluginManager
from backend.core.pipeline.executor import PipelineExecutor

logger = get_logger("SparkPipelineJob")

def main():
    logger.info("🚀 [독립형 Spark Job] 파이프라인 분석 프로세스가 분리된 환경에서 시작됩니다...")
    
    try:
        # 설정 로드
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 매니저 및 실행기 초기화
        plugin_manager = PluginManager(global_config=config_data)
        executor = PipelineExecutor(config=config_data, plugin_manager=plugin_manager)
        
        # 파이프라인 전체 단계(Input -> Process -> Detect -> Output) 실행
        executor.execute()
        
        logger.info("✅ [독립형 Spark Job] 파이프라인 처리가 성공적으로 완료되었습니다.")
        
    except Exception as e:
        logger.error(f"❌ [독립형 Spark Job] 실행 중 치명적 오류: {e}")
        sys.exit(1) # 에러 발생 시 OS에 실패(1) 코드 반환

if __name__ == "__main__":
    main()