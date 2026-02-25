import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from backend.core.utils import get_logger

logger = get_logger("Plugin-MLAnomaly")

def get_db_engine(config):
    conf = next((s for s in config.get("sources", []) if s.get("name") == "ueba_mariaDB"), None)
    if not conf: return None
    url = f"mysql+pymysql://{conf['user']}:{conf['password']}@{conf['host']}:{conf['port']}/{conf['database']}"
    return create_engine(url, pool_pre_ping=True)

def execute(spark, current_df, source_name, config):
    try:
        # 1. Spark DF -> 파이썬 리스트 -> Pandas DF (안전한 메모리 변환)
        rows = current_df.collect()
        if not rows: return current_df
        
        data_list = [row.asDict() for row in rows]
        df = pd.DataFrame(data_list)

        current_hour = datetime.now().hour
        is_night = 1 if 0 <= current_hour <= 5 else 0
        
        # 'user' 컬럼이 없을 경우를 대비한 방어 코드
        user_counts = df.groupby('user').size() if 'user' in df.columns else pd.Series(dtype=int)
        avg_batch_count = user_counts.mean() if not user_counts.empty else 0
        
        logger.info(f"🤖 [{source_name}] 머신러닝(ML) 기반 지표 분석 중... (대상: {len(df)}건)")

        # ⭐️ AI 자연어 사유 생성 로직
        def calculate_score(row):
            # 이전 단계(rule_engine 등)에서 누적된 스코어 확보
            score = float(row.get('risk_score', 0.0))
            contexts = []
            
            user = row.get('user', '')
            if user and not user_counts.empty:
                user_count = user_counts.get(user, 0)
                if avg_batch_count > 0 and user_count > (avg_batch_count * 3):
                    score += 40
                    contexts.append(f"평소 대비 비정상적인 행위 폭증({user_count}건)")
            
            res_val = str(row.get('resource', '')).lower()
            if any(ext in res_val for ext in ['.sql', 'admin', 'backup']):
                score += 50
                contexts.append(f"인가되지 않은 민감 리소스({res_val}) 접근")
                
            if is_night:
                score += 20
                contexts.append("비업무 심야 시간대(00~05시) 활동")
                
            if score >= 70:
                ai_reason = f"[AI 행위 분석] {', '.join(contexts)} 패턴이 복합적으로 식별되었습니다. 내부자 권한 남용 또는 자격 증명 탈취가 의심됩니다."
            else:
                ai_reason = ", ".join(contexts) if contexts else "정상 범주"
                
            return pd.Series([score, ai_reason])

        # Pandas apply 결과를 두 개의 컬럼으로 깔끔하게 확장(expand)
        df[['risk_score', 'anomaly_reason']] = df.apply(calculate_score, axis=1, result_type='expand')
        
        # 2. 고위험군 DB 적재 (HR 데이터 조인)
        db_engine = get_db_engine(config)
        anomalies = df[df['risk_score'] >= 70].copy()
        
        if not anomalies.empty and db_engine:
            with db_engine.begin() as conn:
                for _, row in anomalies.iterrows():
                    conn.execute(text("""
                        INSERT INTO sj_ueba_anomalies (
                            user, risk_score, anomaly_reason, source_name, timestamp,
                            emp_id, dept_name, dept_code
                        )
                        SELECT 
                            :u, :s, :r, :src, NOW(),
                            h.emp_id, h.dept_name, h.dept_code
                        FROM (SELECT :u AS u_name) AS tmp
                        LEFT JOIN sj_ueba_hr h ON h.user_name = tmp.u_name
                    """), {
                        "u": row.get('user', 'Unknown'), 
                        "s": row['risk_score'], 
                        "r": row['anomaly_reason'], 
                        "src": source_name
                    })
            logger.warning(f"🚨 [Anomaly Detected] {len(anomalies)}건 적발 및 DB 기록 완료 ({source_name})")

        # 3. Spark 호환성을 위한 결측치 정리 후 복구
        df = df.fillna("").astype(str)
        df = df.replace({'nan': '', 'None': '', '<NA>': ''})
        
        dict_list = df.to_dict(orient='records')
        return spark.createDataFrame(dict_list) if dict_list else current_df

    except Exception as e:
        logger.error(f"❌ ML Anomaly 분석 모듈 실행 실패: {e}")
        return current_df