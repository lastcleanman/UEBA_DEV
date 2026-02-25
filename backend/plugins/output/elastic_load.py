import os
import math
from datetime import datetime
from elasticsearch import Elasticsearch, helpers
from backend.core.utils import get_logger

logger = get_logger("Plugin-ElasticLoad")

def execute(spark, df, source_name, config):
    try:
        sys_conf = config.get("system", {})
        es_host = sys_conf.get("es_host")
        es_port = sys_conf.get("es_port")

        if not es_host or not es_port:
            logger.warning(f"⏩ [{source_name}] ueba_settings.json에 ES 설정이 없어 적재를 건너뜁니다.")
            return df

        es = Elasticsearch(hosts=[f"http://{es_host}:{es_port}"])
        index_name = f"ueba_{source_name.lower()}_{datetime.now().strftime('%Y%m')}"
        
        # Spark에서 바로 데이터를 꺼냅니다. (Py4J 에러 원천 차단)
        rows = df.collect()
        if not rows:
            return df
            
        actions = []
        for row in rows:
            row_dict = row.asDict()
            clean_row = {}
            
            # ES 매핑 에러 방어: None, 빈 문자열, nan 글자 등을 걸러냅니다.
            for k, v in row_dict.items():
                if v in [None, "", "nan", "None", "<NA>"]:
                    continue
                # float 형의 수학적 NaN 체크 방어
                if isinstance(v, float) and math.isnan(v):
                    continue
                clean_row[k] = v
            
            if clean_row:
                actions.append({
                    "_index": index_name,
                    "_source": clean_row
                })

        # ES 대량 적재 실행
        if actions:
            success, failed = helpers.bulk(es, actions, stats_only=False, raise_on_error=False)
            if failed:
                logger.warning(f"⚠️ [{source_name}] ES 적재 중 일부 오류 발생 ({len(failed)}건 실패)")
            else:
                logger.info(f"✅ [{source_name}] Elasticsearch 적재 완료 ({success}건) -> {index_name}")

    except Exception as e:
        logger.error(f"❌ [{source_name}] Elasticsearch 적재 실패: {e}")
        
    return df