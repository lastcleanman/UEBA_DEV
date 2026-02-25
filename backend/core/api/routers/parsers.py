from fastapi import APIRouter, Request
import glob
import os
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from backend.core.config import PARSER_DIR

router = APIRouter()

@router.get("/api/parsers")
def get_parser_xmls():
    parsers = {}
    xml_files = glob.glob(os.path.join(PARSER_DIR, "*.xml"))
    for file_path in xml_files:
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                parsers[filename] = f.read()
        except Exception as e:
            parsers[filename] = f"<Error>읽기 실패: {str(e)}</Error>"
            
    if parsers: return {"parsers": parsers}
        
    # 기존 원본 로그 파서 생성 로직...
    log_files = glob.glob("/UEBA_DEV/backend/data/**/*log*", recursive=True) + \
                glob.glob("/UEBA_DEV/backend/data/**/*.json", recursive=True) + \
                glob.glob("/UEBA_DEV/backend/data/**/*.csv", recursive=True)
                
    for file_path in log_files:
        if os.path.isdir(file_path): continue
        filename = os.path.basename(file_path)
        if filename.endswith('.parquet') or filename.endswith('.flag') or filename.endswith('.xml'): continue
            
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
                    for k, v in data.items(): xml_content += f'    <Field name="{k}" type="{type(v).__name__}" />\n'
                elif ',' in first_line: 
                    xml_content += '  <Format>CSV</Format>\n  <Fields>\n'
                    for h in first_line.split(','): xml_content += f'    <Field name="{h.strip()}" type="string" />\n'
                else: 
                    xml_content += '  <Format>TEXT</Format>\n  <Fields>\n'
                    for i, p in enumerate(first_line.split()[:5]): xml_content += f'    <Field name="field_{i}" sample_value="{p[:10]}" type="string" />\n'
                xml_content += '  </Fields>\n</LogParser>'
            
            with open(xml_path, 'w', encoding='utf-8') as xf: xf.write(xml_content)
            parsers[xml_filename] = xml_content
        except Exception as e: pass
            
    if not parsers: return {"parsers": {"info.xml": "<Info>파서를 생성할 수 없습니다.</Info>"}}
    return {"parsers": parsers}

@router.post("/api/parsers/update-fields")
async def update_parser_fields(request: Request):
    data = await request.json()
    filename = data.get("filename") 
    fields = data.get("fields") 
    file_path = os.path.join(PARSER_DIR, filename)

    try:
        root = ET.Element("parser", name=filename.replace('.xml', ''))
        for f in fields: ET.SubElement(root, "field", target=f['target'], source=f['source'])
        
        xml_str = ET.tostring(root, encoding='utf-8')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
        with open(file_path, "w", encoding="utf-8") as f: f.write(pretty_xml)
            
        return {"status": "success", "message": f"✅ {filename} 규칙이 저장되었습니다."}
    except Exception as e: return {"status": "error", "message": str(e)}