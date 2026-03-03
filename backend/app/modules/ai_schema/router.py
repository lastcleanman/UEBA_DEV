import os
import random
import xml.etree.ElementTree as ET
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pydantic import BaseModel
from typing import List

# DB 세션을 가져오는 함수 (core.database에 있다고 가정)
from app.core.database import SessionLocal
from app.models.ai_schema import AISchemaHistory

router = APIRouter(tags=["AI Schema"])

# DB 의존성 주입용 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TrainRequest(BaseModel):
    tenant_id: str
    log_type: str
class SchemaField(BaseModel):
    name: str
    type: str
    confidence: str

class UpdateSchemaRequest(BaseModel):
    file_path: str
    tenant_id: str
    log_type: str
    fields: List[SchemaField]

@router.post("/train")
async def trigger_spark_training(req: TrainRequest, db: Session = Depends(get_db)):
    """
    [TODO: 실제 PySpark spark-submit 연동 예정]
    현재는 Spark가 로그를 분석하여 스키마를 추론했다고 가정하고 XML과 수치를 생성합니다.
    """
    # 1. Spark 학습 결과 시뮬레이션
    accuracy = round(random.uniform(88.0, 99.9), 2)
    processed = random.randint(5000, 50000)

    # 2. XML 스키마 파일 자동 생성
    root = ET.Element("LogSchema", tenant=req.tenant_id, type=req.log_type)
    ET.SubElement(root, "Field", name="timestamp", type="datetime", confidence="99%")
    ET.SubElement(root, "Field", name="user", type="string", confidence="95%")
    ET.SubElement(root, "Field", name="action", type="string", confidence="98%")
    ET.SubElement(root, "Field", name="src_ip", type="ip_address", confidence="92%")
    xml_str = ET.tostring(root, encoding="unicode")

    # 테넌트별 artifacts 폴더에 XML 저장
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"schema_{req.log_type}_{timestamp_str}.xml"
    file_path = f"/UEBA/tenants/{req.tenant_id}/artifacts/parsers/{file_name}"

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(xml_str)

    # 3. DB에 학습 이력 저장
    new_history = AISchemaHistory(
        tenant_id=req.tenant_id,
        log_type=req.log_type,
        accuracy=accuracy,
        processed_count=processed,
        xml_file_path=file_path
    )
    db.add(new_history)
    db.commit()
    db.refresh(new_history)

    return {"status": "success", "data": new_history}

@router.get("/history")
async def get_training_history(tenant_id: str, db: Session = Depends(get_db)):
    """DB에 저장된 특정 테넌트의 AI 학습 이력 목록을 반환합니다."""
    res = db.query(AISchemaHistory).filter(AISchemaHistory.tenant_id == tenant_id).order_by(AISchemaHistory.created_at.desc()).all()
    return {"status": "success", "data": res}

@router.get("/xml")
async def get_xml_content(file_path: str):
    """선택한 XML 파일의 상세 내용을 읽어서 반환합니다."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return {"status": "success", "content": f.read()}
    return {"status": "error", "message": "XML 파일을 찾을 수 없습니다."}

@router.get("/schema-detail")
async def get_schema_detail(file_path: str):
    if not os.path.exists(file_path):
        return {"status": "error", "message": "XML 파일을 찾을 수 없습니다."}
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        fields = []
        for child in root.findall('Field'):
            fields.append({
                "name": child.get("name", ""),
                "type": child.get("type", "string"),
                "confidence": child.get("confidence", "100%")
            })
        return {
            "status": "success", 
            "tenant": root.get("tenant"), 
            "type": root.get("type"), 
            "fields": fields
        }
    except Exception as e:
        return {"status": "error", "message": f"파싱 오류: {str(e)}"}
    
@router.post("/schema-detail")
async def update_schema_detail(req: UpdateSchemaRequest):
    try:
        root = ET.Element("LogSchema", tenant=req.tenant_id, type=req.log_type)
        for f in req.fields:
            ET.SubElement(root, "Field", name=f.name, type=f.type, confidence=f.confidence)
        
        # 들여쓰기를 포함하여 예쁘게 XML 문자열 생성
        import xml.dom.minidom
        xml_str = xml.dom.minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        
        with open(req.file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
            
        return {"status": "success", "message": "스키마가 성공적으로 업데이트되었습니다."}
    except Exception as e:
        return {"status": "error", "message": f"저장 오류: {str(e)}"}