import subprocess
import datetime
from fastapi import APIRouter, BackgroundTasks, HTTPException
from backend.core.config import SPARK_JOB_SCRIPT
from backend.core.utils import get_logger

router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline Execution"])
logger = get_logger("API_Pipeline")

# ⭐️ 파이프라인 상태를 저장하는 메모리 저장소 (DB 연동 전 가벼운 형태)
pipeline_state = {
    "is_running": False,
    "current_stage": "idle", # idle, input, process, detect, output, done
    "start_time": None,
    "end_time": None,
    "last_log": "대기 중",
    "last_exit_code": None
}

def run_spark_job_in_background():
    global pipeline_state
    pipeline_state["is_running"] = True
    pipeline_state["current_stage"] = "init"
    pipeline_state["start_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pipeline_state["message"] = "Spark 분석 파이프라인이 실행 중입니다..."
    pipeline_state["end_time"] = None
    
    submit_cmd = [
        "spark-submit",
        "--master", "spark://ueba-spark:7077",
        "--executor-memory", "1g",
        SPARK_JOB_SCRIPT
    ]
    logger.info(f"▶️ [API Trigger] 백그라운드 Spark-Submit 실행: {' '.join(submit_cmd)}")
    
    try:
        process = subprocess.Popen(
            submit_cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        for line in process.stdout:
            clean_line = line.strip()
            print(f"[Spark-Job] {clean_line}")
            
            pipeline_state["last_log"] = clean_line # 프론트엔드 터미널용 실시간 로그
            
            # 단계 추적 로직
            if "Step 1: 데이터 수집" in clean_line:
                pipeline_state["current_stage"] = "input"
            elif "Step 2: 데이터 정제" in clean_line:
                pipeline_state["current_stage"] = "process"
            elif "Step 3: 위협 탐지" in clean_line:
                pipeline_state["current_stage"] = "detect"
            elif "Step 4: 최종 적재" in clean_line:
                pipeline_state["current_stage"] = "output"
            elif "모든 단계가 성공적으로 완료" in clean_line:
                pipeline_state["current_stage"] = "done"
            
        process.wait()
        
        # ⭐️ 작업 종료 후 상태 업데이트
        pipeline_state["is_running"] = False
        pipeline_state["end_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pipeline_state["last_exit_code"] = process.returncode
        
        if process.returncode == 0:
            pipeline_state["message"] = "✅ 파이프라인 분석이 성공적으로 완료되었습니다."
            logger.info("✅ 백그라운드 파이프라인 분석 종료.")
        else:
            pipeline_state["message"] = f"❌ Spark Job 비정상 종료 (Exit Code: {process.returncode})"
            logger.error(pipeline_state["message"])
            
    except Exception as e:
        pipeline_state["is_running"] = False
        pipeline_state["message"] = f"❌ 치명적 실행 오류: {e}"
        logger.error(pipeline_state["message"])

@router.post("/run")
async def trigger_pipeline(background_tasks: BackgroundTasks):
    """파이프라인 실행을 요청합니다."""
    global pipeline_state
    
    if pipeline_state["is_running"]:
        raise HTTPException(status_code=400, detail="이미 파이프라인이 실행 중입니다. 끝날 때까지 기다려주세요.")
        
    logger.info("🌐 파이프라인 구동 API 호출 수신 (POST /api/v1/pipeline/run)")
    background_tasks.add_task(run_spark_job_in_background)
    
    return {
        "status": "success", 
        "message": "파이프라인 분석 작업이 백그라운드에서 성공적으로 시작되었습니다."
    }

# ⭐️ 새로 추가된 상태 조회 엔드포인트
@router.get("/status")
async def get_pipeline_status():
    """현재 파이프라인의 실행 상태를 반환합니다."""
    return pipeline_state