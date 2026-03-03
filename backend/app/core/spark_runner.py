import subprocess
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("SparkRunner")

class SparkJobRunner:
    """
    FastAPI 서버에서 별도의 PySpark 스크립트를 실행하고, 
    결과(stdout)를 파싱하여 반환하는 Core 유틸리티입니다.
    """
    def __init__(self, python_bin: str = "python3"):
        self.python_bin = python_bin

    def run_job(self, script_path: str, args: List[str]) -> Tuple[bool, str, str]:
        """
        Spark 스크립트를 실행하고 성공 여부와 출력값을 반환합니다.
        return: (is_success, stdout, stderr)
        """
        cmd = [self.python_bin, script_path] + args
        logger.info(f"🚀 Spark Job 실행: {' '.join(cmd)}")
        
        try:
            # 외부 프로세스로 Spark 스크립트 실행 (동기 블로킹 방식, 필요시 비동기 큐 전환 가능)
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode == 0:
                return True, process.stdout.strip(), process.stderr.strip()
            else:
                logger.error(f"❌ Spark Job 에러: {process.stderr}")
                return False, process.stdout.strip(), process.stderr.strip()
                
        except Exception as e:
            logger.exception("Spark 프로세스 실행 중 치명적 오류 발생")
            return False, "", str(e)

# 전역에서 공유할 싱글톤 인스턴스
spark_runner = SparkJobRunner()