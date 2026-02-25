from pyspark.sql.functions import col, regexp_extract, lit
from backend.core.utils import get_logger

logger = get_logger("Plugin-Process")

# ⭐️ executor에서 넘겨주는 source_name 파라미터를 추가로 받습니다.
def execute(spark, df, source_name):
    logger.info(f"⚙️ [{source_name}] 데이터 정제 시작 (입력: {df.count()}건)")
    
    try:
        cols = df.columns
        last_col = cols[-1] # 사용자정의 필드는 항상 마지막에 위치
        
        # IP 추출 로직: Web/Auth 로그는 5번(Client IP)이 존재하지만 시스템 로그는 없으므로 3번(Mgmt IP) 사용
        ip_col = cols[5] if source_name in ["Auth_Logs", "Web_Logs"] and len(cols) > 5 else cols[3]

        # ⭐️ UEBA 표준 5칸 포맷으로 강제 변환
        parsed_df = df.select(
            lit(source_name).alias("source"),                          # 1. 출처 (Auth, Web 등)
            col(cols[0]).alias("event_type"),                          # 2. 이벤트 타입 (AUDIT, DETECT 등)
            col(cols[2]).alias("timestamp"),                           # 3. 시간
            col(ip_col).alias("src_ip"),                               # 4. IP
            regexp_extract(col(last_col), r"USER_ID=(SJ_[0-9]+)", 1).alias("user_id") # 5. 사번 추출
        )
        
        # 사번이 정규식으로 예쁘게 추출된 '진짜 데이터'만 필터링
        parsed_df = parsed_df.filter(col("user_id") != "")
        
        valid_count = parsed_df.count()
        logger.info(f"✅ [{source_name}] 정제 완료 (유효 데이터: {valid_count}건)")
        
        return parsed_df

    except Exception as e:
        logger.error(f"❌ [{source_name}] 정제 중 오류 발생: {e}")
        return None