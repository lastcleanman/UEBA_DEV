import os
from datetime import datetime
from elasticsearch import Elasticsearch, helpers
from core.utils import get_logger

logger = get_logger("Plugin-ElasticLoad")

def execute(spark, df, source_name, global_config):
    try:
        sys_conf = global_config.get("system", {})
        es_host = sys_conf.get("es_host")
        es_port = sys_conf.get("es_port")

        if not es_host or not es_port:
            logger.error("❌ ueba_settings.json 파일의 'system' 블록에 es_host 또는 es_port 설정이 누락되었습니다.")
            return df

        es = Elasticsearch(hosts=[f"http://{es_host}:{es_port}"])
        index_name = f"ueba_{source_name.lower()}_{datetime.now().strftime('%Y%m')}"
        
        # ⭐️ [핵심 수정] df.toPandas()를 쓰지 않고 Spark에서 바로 데이터를 꺼냅니다! (Py4J 에러 원천 차단)
        rows = df.collect()
        
        actions = []
        for row in rows:
            row_dict = row.asDict()
            clean_row = {}
            
            # ES 매핑 에러 방어: None, 빈 문자열, nan 글자 등을 걸러내고 유효한 값만 담습니다.
            for k, v in row_dict.items():
                if v is not None and v != "" and v != "nan" and v != "None" and v != "<NA>":
                    # float 형의 NaN 체크 방어 (v != v 는 v가 NaN일 때만 True가 됩니다)
                    if isinstance(v, float) and v != v:
                        continue
                    clean_row[k] = v
            
            # 깨끗해진 데이터만 ES 전송 목록에 담기
            if clean_row:
                actions.append({
                    "_index": index_name,
                    "_source": clean_row
                })

        # ES 대량 적재 실행
        if actions:
            success, failed = helpers.bulk(es, actions, stats_only=False, raise_on_error=False)
            if failed:
                logger.warning(f"⚠️ ES 적재 중 일부 오류 발생 ({len(failed)}건 실패)")
                logger.debug(f"🔍 ES 에러 상세: {failed[0]}") 
            else:
                logger.info(f"✅ Elasticsearch 적재 완료 ({success}건) -> {index_name} (Host: {es_host}:{es_port})")
        else:
            logger.warning(f"⚠️ [{source_name}] 적재할 유효한 데이터가 없습니다.")

    except Exception as e:
        logger.error(f"❌ Elasticsearch 적재 실패: {e}")
        
    return df