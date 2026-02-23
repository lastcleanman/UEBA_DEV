from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import threading
import glob
import json
import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
from sqlalchemy import create_engine, text

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LOG_FILE = "/UEBA_DEV/logs/ueba_engine.log"
DATA_DIR = "/UEBA_DEV/data"
MODE_FILE = os.path.join(DATA_DIR, "mode.txt")
CONFIG_FILE = "/UEBA_DEV/conf/ueba_settings.json" # ⭐️ 추가됨

# 초기 기동 시 모드 파일이 없으면 생성
if not os.path.exists(MODE_FILE):
    with open(MODE_FILE, "w") as f: f.write("manual")

# ==========================================
# ⭐️ 누락되었던 DB 연결용 필수 함수 추가
# ==========================================
def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f: 
        return json.load(f)

def get_db_engine(config):
    conf = next((s for s in config.get("sources", []) if s.get("name") == "ueba_mariaDB"), None)
    if not conf: return None
    url = f"mysql+pymysql://{conf['user']}:{conf['password']}@{conf['host']}:{conf['port']}/{conf['database']}"
    return create_engine(url, pool_pre_ping=True)
# ==========================================

@app.get("/api/logs")
def get_logs(lines: int = 200):
    if not os.path.exists(LOG_FILE):
        return {"logs": ["⏳ 로그 대기 중..."]}
    try:
        result = subprocess.run(['tail', '-n', str(lines), LOG_FILE], capture_output=True, text=True)
        return {"logs": result.stdout.split('\n')}
    except Exception as e: return {"logs": [f"❌ 로그 읽기 실패: {e}"]}

@app.get("/api/mode")
def get_mode():
    try:
        with open(MODE_FILE, "r") as f: return {"mode": f.read().strip()}
    except: return {"mode": "manual"}

@app.post("/api/mode/{new_mode}")
def set_mode(new_mode: str):
    if new_mode not in ["daemon", "manual"]:
        return {"status": "error", "message": "잘못된 모드입니다."}
    try:
        with open(MODE_FILE, "w") as f: f.write(new_mode)
        return {"status": "success", "message": f"✅ {new_mode.upper()} 모드로 변경되었습니다."}
    except Exception as e: return {"status": "error", "message": str(e)}

def trigger_task(stage_id):
    try:
        if stage_id in ["all", "input"]:
            subprocess.run(["python3", "/UEBA_DEV/tools/generate_multi_logs.py"])
        flag_path = os.path.join(DATA_DIR, f"trigger_{stage_id}.flag")
        open(flag_path, 'w').close()
    except Exception as e: print(e)

@app.post("/api/trigger/{stage_id}")
def trigger_pipeline(stage_id: str):
    threading.Thread(target=trigger_task, args=(stage_id,)).start()
    return {"status": "success", "message": f"✅ [{stage_id.upper()}] 수동 실행 신호 전송 완료!"}

@app.get("/api/parsers")
def get_parser_xmls():
    parsers = {}
    PARSER_DIR = "/UEBA_DEV/conf/parsers"
    os.makedirs(PARSER_DIR, exist_ok=True)
    
    xml_files = glob.glob(os.path.join(PARSER_DIR, "*.xml"))
    for file_path in xml_files:
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                parsers[filename] = f.read()
        except Exception as e:
            parsers[filename] = f"<Error>읽기 실패: {str(e)}</Error>"
            
    if parsers:
        return {"parsers": parsers}
        
    log_files = glob.glob("/UEBA_DEV/data/**/*log*", recursive=True) + \
                glob.glob("/UEBA_DEV/data/**/*.json", recursive=True) + \
                glob.glob("/UEBA_DEV/data/**/*.csv", recursive=True)
                
    for file_path in log_files:
        if os.path.isdir(file_path): continue
        filename = os.path.basename(file_path)
        
        if filename.endswith('.parquet') or filename.endswith('.flag') or filename.endswith('.xml'):
            continue
            
        xml_filename = f"{filename.split('.')[0]}.xml" 
        xml_path = os.path.join(PARSER_DIR, xml_filename)
        xml_content = f'<?xml version="1.0" encoding="UTF-8"?>\n<LogParser name="{filename}">\n'
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if not first_line: continue
                
                if first_line.startswith('{'): 
                    xml_content += '  <Format>JSON</Format>\n  <Fields>\n'
                    data = json.loads(first_line)
                    for k, v in data.items():
                        xml_content += f'    <Field name="{k}" type="{type(v).__name__}" />\n'
                elif ',' in first_line: 
                    xml_content += '  <Format>CSV</Format>\n  <Fields>\n'
                    for h in first_line.split(','):
                        xml_content += f'    <Field name="{h.strip()}" type="string" />\n'
                else: 
                    xml_content += '  <Format>TEXT</Format>\n  <Fields>\n'
                    for i, p in enumerate(first_line.split()[:5]):
                        xml_content += f'    <Field name="field_{i}" sample_value="{p[:10]}" type="string" />\n'
                        
            xml_content += '  </Fields>\n</LogParser>'
            
            with open(xml_path, 'w', encoding='utf-8') as xf:
                xf.write(xml_content)
            parsers[xml_filename] = xml_content
            
        except Exception as e:
            pass
            
    if not parsers:
        return {"parsers": {"info.xml": "<Info>데이터 폴더에 원본 로그가 없어 파서를 생성할 수 없습니다.</Info>"}}
        
    return {"parsers": parsers}

@app.get("/api/ml-metrics")
async def get_ml_metrics():
    try:
        db_engine = get_db_engine(load_config())
        if not db_engine:
            raise Exception("DB 설정을 찾을 수 없습니다.")

        with db_engine.connect() as conn:
            # 1. 총 데이터 계산
            total_res = conn.execute(text("SELECT SUM(processed_count) FROM sj_ueba_ingestion_history")).fetchone()
            total_count = int(total_res[0]) if total_res and total_res[0] is not None else 0

            # 2. 고위험군 카운트
            count_res = conn.execute(text("SELECT COUNT(*) FROM sj_ueba_anomalies WHERE risk_score >= 70")).fetchone()
            high_risk_count = int(count_res[0]) if count_res and count_res[0] is not None else 0

            # 3. 고위험군 리스트
            query = text("SELECT user, risk_score, anomaly_reason, timestamp FROM sj_ueba_anomalies WHERE risk_score >= 70 ORDER BY timestamp DESC LIMIT 5")
            result = conn.execute(query).fetchall()
            
            detection_list = []
            for row in result:
                ts_str = str(row[3]) if row[3] else ""
                time_only = ts_str.split(" ")[1][:8] if " " in ts_str else ts_str 

                detection_list.append({
                    "time": time_only,
                    "user": str(row[0]),
                    "risk_score": float(row[1]),
                    "reason": str(row[2])
                })

            anomaly_rate = round((high_risk_count / total_count * 100), 2) if total_count > 0 else 0.0

            return {
                "total_analyzed": total_count,
                "high_risk_count": high_risk_count,
                "anomaly_rate": anomaly_rate,
                "status": "실시간 스트리밍 학습 중",
                "detection_list": detection_list
            }
            
    except Exception as e:
        print(f"❌ ML Metrics API Error: {e}") 
        return {
            "total_analyzed": 0, 
            "high_risk_count": 0, 
            "anomaly_rate": 0.0, 
            "status": "에러 발생", 
            "detection_list": [],
            "error_detail": str(e)
        }

@app.post("/api/parsers/update-fields")
async def update_parser_fields(request: Request):
    data = await request.json()
    filename = data.get("filename") 
    fields = data.get("fields") 

    PARSER_DIR = "/UEBA_DEV/conf/parsers"
    file_path = os.path.join(PARSER_DIR, filename)

    try:
        root = ET.Element("parser", name=filename.replace('.xml', ''))
        for f in fields:
            ET.SubElement(root, "field", target=f['target'], source=f['source'])
        
        xml_str = ET.tostring(root, encoding='utf-8')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)
            
        return {"status": "success", "message": f"✅ {filename} 규칙이 물리 파일에 저장되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/anomalies/all")
async def get_all_anomalies(limit: int = 1000):
    try:
        db_engine = get_db_engine(load_config())
        with db_engine.connect() as conn:
            # 70점 이상인 모든 내역을 최신순으로 가져옴
            query = text(f"SELECT user, risk_score, anomaly_reason, timestamp FROM sj_ueba_anomalies WHERE risk_score >= 70 ORDER BY timestamp DESC LIMIT {limit}")
            result = conn.execute(query).fetchall()
            
            all_list = []
            for row in result:
                ts_str = str(row[3]) if row[3] else ""
                time_only = ts_str.split(" ")[1][:8] if " " in ts_str else ts_str 

                all_list.append({
                    "time": time_only,
                    "user": str(row[0]),
                    "risk_score": float(row[1]),
                    "reason": str(row[2])
                })

            return {"status": "success", "data": all_list}
            
    except Exception as e:
        print(f"❌ 전체 이상행위 조회 API 에러: {e}") 
        return {"status": "error", "data": []}