import re
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("Normalizer")

class LogNormalizer:
    """
    원시 로그(Raw String)를 UEBA 표준 스키마(JSON/Dict)로 변환하는 정제 엔진입니다.
    Key-Value 쌍 추출 및 Regex 정규표현식 파싱을 지원합니다.
    """
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    def normalize(self, raw_data: str, rule_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """설정된 규칙에 따라 단일 로그를 파싱합니다."""
        if not raw_data:
            return {}

        rule_type = rule_config.get("type", "kv") # 기본값을 Key-Value로 설정
        
        try:
            if rule_type == "kv":
                return self._parse_key_value(
                    raw_data, 
                    separator=rule_config.get("separator", "="), 
                    delimiter=rule_config.get("delimiter", " ")
                )
            elif rule_type == "regex":
                return self._parse_regex(
                    raw_data, 
                    pattern=rule_config.get("pattern", ""), 
                    fields=rule_config.get("fields", [])
                )
            else:
                logger.warning(f"[{self.tenant_id}] 지원하지 않는 파싱 타입: {rule_type}")
                return None
                
        except Exception as e:
            logger.error(f"[{self.tenant_id}] 로그 파싱 오류: {e} | Data: {raw_data}")
            return None

    def _parse_key_value(self, raw_data: str, separator: str, delimiter: str) -> Dict[str, Any]:
        """Key-Value 형태(예: user=admin action=login) 파싱"""
        parsed = {}
        # 구분자(예: 공백)로 먼저 나눔
        pairs = raw_data.split(delimiter)
        for pair in pairs:
            if separator in pair:
                # 첫 번째 separator(예: =)만 기준으로 나눔
                k, v = pair.split(separator, 1)
                parsed[k.strip()] = v.strip()
        return parsed

    def _parse_regex(self, raw_data: str, pattern: str, fields: list[str]) -> Dict[str, Any]:
        """정규표현식을 이용한 복잡한 로그 파싱"""
        if not pattern:
            return {}
            
        match = re.search(pattern, raw_data)
        if match:
            groups = match.groups()
            # 정규식 괄호() 그룹 순서대로 필드명 매핑
            return {fields[i]: groups[i] for i in range(min(len(fields), len(groups)))}
        return {}