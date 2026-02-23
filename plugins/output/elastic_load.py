import urllib.request, json
from core.utils import get_logger

logger = get_logger("Plugin-ElasticLoad")

def execute(df, global_config):
    try:
        count = df.count()
        if count == 0: return df
        sys_conf = global_config.get("system", {})
        host, port, index = sys_conf.get("es_host"), sys_conf.get("es_port"), sys_conf.get("es_index")
        
        # ⭐️ 오류가 나는 df.toPandas() 대신 df.collect()로 Python Dict 형태로 바로 변환
        records = [row.asDict() for row in df.collect()]
        
        bulk_data = "".join([f'{json.dumps({"index": {"_index": index}})}\n{json.dumps({k: v.isoformat() if hasattr(v, "isoformat") else v for k, v in r.items() if v is not None})}\n' for r in records])

        req = urllib.request.Request(f"http://{host}:{port}/_bulk", data=bulk_data.encode('utf-8'), method='POST')
        req.add_header('Content-Type', 'application/x-ndjson')
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            if res_data.get('errors'): 
                logger.warning("⚠️ ES 적재 중 일부 오류 발생")
            else: 
                logger.info(f"✅ Elasticsearch 적재 완료 ({count}건)")
                
    except Exception as e: 
        logger.error(f"❌ ES 적재 실패: {e}")
        
    return df