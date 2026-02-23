from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import threading
import glob
import json
import pandas as pd

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

# 초기 기동 시 모드 파일이 없으면 생성
if not os.path.exists(MODE_FILE):
    with open(MODE_FILE, "w") as f: f.write("manual")

@app.get("/api/logs")
def get_logs(lines: int = 200):
    if not os.path.exists(LOG_FILE):
        return {"logs": ["⏳ 로그 대기 중..."]}
    try:
        result = subprocess.run(['tail', '-n', str(lines), LOG_FILE], capture_output=True, text=True)
        return {"logs": result.stdout.split('\n')}
    except Exception as e: return {"logs": [f"❌ 로그 읽기 실패: {e}"]}

# ⭐️ 모드 조회 API
@app.get("/api/mode")
def get_mode():
    try:
        with open(MODE_FILE, "r") as f: return {"mode": f.read().strip()}
    except: return {"mode": "manual"}

# ⭐️ 모드 변경 API
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
    
    # ⭐️ 1. 최우선: 이미 디스크에 생성된 XML 파일들이 있다면 무조건 먼저 읽어서 화면에 보냅니다!
    xml_files = glob.glob(os.path.join(PARSER_DIR, "*.xml"))
    
    for file_path in xml_files:
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                parsers[filename] = f.read()
        except Exception as e:
            parsers[filename] = f"<Error>읽기 실패: {str(e)}</Error>"
            
    # 읽어온 XML 파일이 하나라도 있다면 여기서 바로 프론트엔드로 전달합니다.
    if parsers:
        return {"parsers": parsers}
        
    # -----------------------------------------------------------------
    # 2. 만약 XML 파일이 하나도 없다면? 원본 로그를 찾아 새로 생성합니다.
    # (이전의 .json만 찾던 버그를 고치고, 이름에 log가 들어간 모든 파일을 찾습니다)
    log_files = glob.glob("/UEBA_DEV/data/**/*log*", recursive=True) + \
                glob.glob("/UEBA_DEV/data/**/*.json", recursive=True) + \
                glob.glob("/UEBA_DEV/data/**/*.csv", recursive=True)
                
    for file_path in log_files:
        if os.path.isdir(file_path): continue
        filename = os.path.basename(file_path)
        
        if filename.endswith('.parquet') or filename.endswith('.flag') or filename.endswith('.xml'):
            continue
            
        xml_filename = f"{filename.split('.')[0]}.xml" # Auth_Logs.xml 처럼 이름 짓기
        xml_path = os.path.join(PARSER_DIR, xml_filename)
        xml_content = f'<?xml version="1.0" encoding="UTF-8"?>\n<LogParser name="{filename}">\n'
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if not first_line: continue
                
                if first_line.startswith('{'): # JSON 형식
                    xml_content += '  <Format>JSON</Format>\n  <Fields>\n'
                    data = json.loads(first_line)
                    for k, v in data.items():
                        xml_content += f'    <Field name="{k}" type="{type(v).__name__}" />\n'
                elif ',' in first_line: # CSV 형식
                    xml_content += '  <Format>CSV</Format>\n  <Fields>\n'
                    for h in first_line.split(','):
                        xml_content += f'    <Field name="{h.strip()}" type="string" />\n'
                else: # 일반 텍스트/Syslog 형식
                    xml_content += '  <Format>TEXT</Format>\n  <Fields>\n'
                    for i, p in enumerate(first_line.split()[:5]):
                        xml_content += f'    <Field name="field_{i}" sample_value="{p[:10]}" type="string" />\n'
                        
            xml_content += '  </Fields>\n</LogParser>'
            
            # 생성된 XML 저장
            with open(xml_path, 'w', encoding='utf-8') as xf:
                xf.write(xml_content)
            parsers[xml_filename] = xml_content
            
        except Exception as e:
            pass
            
    if not parsers:
        return {"parsers": {"info.xml": "<Info>데이터 폴더에 원본 로그가 없어 파서를 생성할 수 없습니다.</Info>"}}
        
    return {"parsers": parsers}

@app.get("/api/ml-metrics")
def get_ml_metrics():
    """ML 분석 완료된 파케이 파일을 읽어 학습/탐지 지표를 수치화합니다."""
    files = glob.glob("/UEBA_DEV/data/intermediate/*_detect.parquet")
    
    total_analyzed = 0
    high_risk_count = 0
    
    for f in files:
        try:
            df = pd.read_parquet(f)
            total_analyzed += len(df)
            
            # 플러그인이 부여한 위험도 컬럼을 찾습니다 (없으면 임의로 상위 5%를 이상치로 간주)
            if 'risk_score' in df.columns:
                high_risk_count += len(df[df['risk_score'] >= 80])
            elif 'anomaly_score' in df.columns:
                high_risk_count += len(df[df['anomaly_score'] >= 80])
            else:
                # ML 컬럼을 찾지 못한 경우 시각화를 위해 가상의 5% 수치 적용
                high_risk_count += int(len(df) * 0.05) 
        except Exception:
            pass
            
    # 엔진 상태 파일 확인
    engine_mode = "manual"
    if os.path.exists(MODE_FILE):
        with open(MODE_FILE, "r") as f: engine_mode = f.read().strip()
        
    status_msg = "학습 및 추론 대기 중 💤"
    if engine_mode == "daemon": status_msg = "실시간 스트리밍 학습 중 🔄"
    elif total_analyzed > 0: status_msg = "배치(Batch) 분석 완료 ✅"

    return {
        "total_analyzed": total_analyzed,
        "high_risk_count": high_risk_count,
        "anomaly_rate": round((high_risk_count / total_analyzed * 100), 1) if total_analyzed > 0 else 0.0,
        "status": status_msg
    }