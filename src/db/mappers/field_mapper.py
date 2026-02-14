"""
필드 매핑 유틸리티

스키마와 시트 필드 간의 매핑을 담당하는 유틸리티 클래스입니다.
데이터 타입 변환, 필드 유효성 검사, 자동 매핑 기능을 제공합니다.
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime


class FieldMapper:
    """
    스키마 기반 필드 매핑 클래스
    
    스키마와 시트 필드 간의 데이터 변환을 담당합니다.
    """
    
    def __init__(self, schema_registry=None):
        """
        FieldMapper 초기화
        
        Args:
            schema_registry: 스키마 레지스트리 (선택사항)
        """
        self.schema_registry = schema_registry
        self.logger = logging.getLogger(__name__)
        
        # 데이터 타입 변환기
        self.type_converters = {
            'string': self._convert_to_string,
            'integer': self._convert_to_integer,
            'decimal': self._convert_to_decimal,
            'datetime': self._convert_to_datetime,
            'boolean': self._convert_to_boolean,
            'enum': self._convert_to_string
        }
    
    def map_to_sheet(self, data: Dict[str, Any], sheet_name: str) -> List[Any]:
        """
        데이터를 시트 형식으로 매핑
        
        Args:
            data: 변환할 데이터
            sheet_name: 시트 이름
            
        Returns:
            List[Any]: 시트 형식의 데이터
        """
        try:
            if self.schema_registry:
                schema = self.schema_registry.get_schema(sheet_name)
                field_order = list(schema.get('fields', {}).keys())
            else:
                # 스키마가 없으면 데이터의 키 순서 사용
                field_order = list(data.keys())
            
            row_data = []
            for field in field_order:
                value = data.get(field, "")
                if value is None:
                    value = ""
                elif isinstance(value, bool):
                    value = "TRUE" if value else "FALSE"
                else:
                    value = str(value)
                row_data.append(value)
            
            self.logger.debug(f"Mapped data to sheet format: {len(row_data)} fields")
            return row_data
            
        except Exception as e:
            self.logger.error(f"Failed to map data to sheet: {str(e)}")
            raise
    
    def map_from_sheet(self, row: List[Any], sheet_name: str) -> Dict[str, Any]:
        """
        시트 데이터를 객체 형식으로 매핑
        
        Args:
            row: 시트 행 데이터
            sheet_name: 시트 이름
            
        Returns:
            Dict[str, Any]: 객체 형식의 데이터
        """
        try:
            if self.schema_registry:
                schema = self.schema_registry.get_schema(sheet_name)
                fields = schema.get('fields', {})
            else:
                # 스키마가 없으면 기본 필드 사용
                fields = {f"field_{i}": {'type': 'string'} for i in range(len(row))}
            
            result = {}
            field_names = list(fields.keys())
            
            for i, field_name in enumerate(field_names):
                if i < len(row):
                    value = row[i]
                    field_type = fields[field_name].get('type', 'string')
                    converted_value = self._convert_value(value, field_type)
                    result[field_name] = converted_value
                else:
                    result[field_name] = None
            
            self.logger.debug(f"Mapped data from sheet format: {len(result)} fields")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to map data from sheet: {str(e)}")
            raise
    
    def validate_data(self, data: Dict[str, Any], sheet_name: str) -> bool:
        """
        데이터 유효성 검사
        
        Args:
            data: 검증할 데이터
            sheet_name: 시트 이름
            
        Returns:
            bool: 유효성 여부
        """
        try:
            if not self.schema_registry:
                return True  # 스키마가 없으면 통과
            
            schema = self.schema_registry.get_schema(sheet_name)
            fields = schema.get('fields', {})
            
            for field_name, field_config in fields.items():
                value = data.get(field_name)
                
                # 필수 필드 검사
                if field_config.get('required', False) and (value is None or value == ""):
                    self.logger.warning(f"Required field '{field_name}' is missing or empty")
                    return False
                
                # 데이터 타입 검사
                if value is not None and value != "":
                    field_type = field_config.get('type', 'string')
                    if not self._validate_type(value, field_type, field_config):
                        self.logger.warning(f"Field '{field_name}' has invalid type")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Data validation failed: {str(e)}")
            return False
    
    def _convert_value(self, value: Any, target_type: str) -> Any:
        """
        값 타입 변환
        
        Args:
            value: 변환할 값
            target_type: 목표 타입
            
        Returns:
            Any: 변환된 값
        """
        if value is None or value == "":
            return None
        
        converter = self.type_converters.get(target_type, self._convert_to_string)
        return converter(value)
    
    def _convert_to_string(self, value: Any) -> str:
        """문자열로 변환"""
        return str(value)
    
    def _convert_to_integer(self, value: Any) -> Optional[int]:
        """정수로 변환"""
        try:
            if isinstance(value, str):
                value = value.replace(',', '')
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _convert_to_decimal(self, value: Any) -> Optional[float]:
        """소수로 변환"""
        try:
            if isinstance(value, str):
                value = value.replace(',', '')
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _convert_to_datetime(self, value: Any) -> Optional[datetime]:
        """날짜시간으로 변환"""
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            # 다양한 날짜 형식 처리
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%Y/%m/%d %H:%M:%S',
                '%Y/%m/%d %H:%M',
                '%Y/%m/%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        
        return None
    
    def _convert_to_boolean(self, value: Any) -> bool:
        """불리언으로 변환"""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on']
        
        return bool(value)
    
    def _validate_type(self, value: Any, field_type: str, field_config: Dict[str, Any]) -> bool:
        """
        데이터 타입 유효성 검사
        
        Args:
            value: 검증할 값
            field_type: 필드 타입
            field_config: 필드 설정
            
        Returns:
            bool: 유효성 여부
        """
        try:
            if field_type == 'enum':
                allowed_values = field_config.get('values', [])
                return value in allowed_values
            
            elif field_type == 'string':
                return isinstance(value, str)
            
            elif field_type == 'integer':
                return self._convert_to_integer(value) is not None
            
            elif field_type == 'decimal':
                return self._convert_to_decimal(value) is not None
            
            elif field_type == 'datetime':
                return self._convert_to_datetime(value) is not None
            
            elif field_type == 'boolean':
                return isinstance(value, bool) or str(value).lower() in ['true', 'false', '1', '0']
            
            return True
            
        except Exception:
            return False
