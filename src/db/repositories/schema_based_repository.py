"""
Schema-Based Repository

스키마 기반의 범용 리포지토리 구현.
"""

from __future__ import annotations

from typing import Dict, Any, List
from pathlib import Path

from .base_repository import BaseSheetRepository
from ...config.schema_loader import get_schema_loader


class SchemaBasedRepository(BaseSheetRepository):
    """
    스키마 기반 리포지토리
    
    스키마 파일을 기반으로 동적으로 시트 구조를 처리합니다.
    """
    
    def __init__(self, client, spreadsheet_id: str, sheet_key: str, project_root: Path):
        """
        SchemaBasedRepository 초기화
        
        Args:
            client: Google Sheets 클라이언트
            spreadsheet_id: 스프레드시트 ID
            sheet_key: 스키마 키 (예: 'Portfolio', 'Performance')
            project_root: 프로젝트 루트 경로
        """
        # 부모 클래스 초기화 (sheet_name은 스키마에서 가져옴)
        schema_loader = get_schema_loader(project_root)
        sheet_config = schema_loader.get_sheet_config(sheet_key)
        
        if not sheet_config:
            raise ValueError(f"Sheet config not found for key: {sheet_key}")
        
        super().__init__(client, spreadsheet_id, sheet_config.sheet_name)
        
        self.sheet_key = sheet_key
        self.project_root = project_root
        self.schema_loader = schema_loader
        self.sheet_config = sheet_config
        
        self.logger.info(f"SchemaBasedRepository initialized for sheet '{sheet_config.sheet_name}' (key: {sheet_key})")
    
    def get_field_mapping(self) -> Dict[str, str]:
        """
        필드 매핑 정보 조회
        
        Returns:
            Dict[str, str]: 필드명 -> 셀 주소 매핑
        """
        return self.schema_loader.get_field_mapping(self.sheet_key)
    
    def update_field(self, field_name: str, value: Any) -> bool:
        """
        필드 값 업데이트
        
        Args:
            field_name: 필드명
            value: 업데이트할 값
            
        Returns:
            bool: 업데이트 성공 여부
        """
        field_mapping = self.get_field_mapping()
        cell_address = field_mapping.get(field_name)
        
        if not cell_address:
            self.logger.error(f"Field mapping not found for field: {field_name}")
            return False
        
        return self.update_cell(cell_address, value)
    
    def get_field_value(self, field_name: str) -> Any:
        """
        필드 값 조회
        
        Args:
            field_name: 필드명
            
        Returns:
            Any: 필드 값
        """
        field_mapping = self.get_field_mapping()
        cell_address = field_mapping.get(field_name)
        
        if not cell_address:
            self.logger.error(f"Field mapping not found for field: {field_name}")
            return None
        
        return self.get_cell_value(cell_address)
    
    def update_block_field(self, block_name: str, field_name: str, value: Any) -> bool:
        """
        블록 필드 값 업데이트 (Dashboard 타입)
        
        Args:
            block_name: 블록명
            field_name: 필드명
            value: 업데이트할 값
            
        Returns:
            bool: 업데이트 성공 여부
        """
        if self.sheet_config.sheet_type != 'dashboard':
            self.logger.error(f"Sheet {self.sheet_key} is not a dashboard type")
            return False
        
        block_config = self.schema_loader.get_block_config(self.sheet_key, block_name)
        if not block_config:
            self.logger.error(f"Block config not found: {block_name}")
            return False
        
        field_address = block_config.fields.get(field_name)
        if not field_address:
            self.logger.error(f"Field mapping not found for block field: {block_name}.{field_name}")
            return False
        
        return self.update_cell(field_address, value)
    
    def get_block_field_value(self, block_name: str, field_name: str) -> Any:
        """
        블록 필드 값 조회 (Dashboard 타입)
        
        Args:
            block_name: 블록명
            field_name: 필드명
            
        Returns:
            Any: 필드 값
        """
        if self.sheet_config.sheet_type != 'dashboard':
            self.logger.error(f"Sheet {self.sheet_key} is not a dashboard type")
            return None
        
        block_config = self.schema_loader.get_block_config(self.sheet_key, block_name)
        if not block_config:
            self.logger.error(f"Block config not found: {block_name}")
            return None
        
        field_address = block_config.fields.get(field_name)
        if not field_address:
            self.logger.error(f"Field mapping not found for block field: {block_name}.{field_name}")
            return None
        
        return self.get_cell_value(field_address)
    
    def update_table_row(self, row_data: Dict[str, Any], row_index: int = None) -> bool:
        """
        테이블 행 업데이트 (Table 타입)
        
        Args:
            row_data: 행 데이터
            row_index: 행 인덱스 (None이면 다음 빈 행)
            
        Returns:
            bool: 업데이트 성공 여부
        """
        if self.sheet_config.sheet_type != 'table':
            self.logger.error(f"Sheet {self.sheet_key} is not a table type")
            return False
        
        field_mapping = self.get_field_mapping()
        
        # 행 인덱스 결정
        if row_index is None:
            row_index = self._get_next_empty_row()
        
        # 데이터 포맷팅
        row_values = []
        for column_letter in field_mapping.values():
            # 컬럼 순서대로 값 정렬
            field_name = next((name for name, addr in field_mapping.items() if addr == column_letter), None)
            if field_name and field_name in row_data:
                row_values.append(row_data[field_name])
            else:
                row_values.append("")
        
        # 범위 계산
        start_col = min(field_mapping.values())
        end_col = max(field_mapping.values())
        range_address = f"{start_col}{row_index}:{end_col}{row_index}"
        
        return self.update_range(range_address, [row_values])
    
    def get_table_data(self) -> List[Dict[str, Any]]:
        """
        테이블 데이터 조회 (Table 타입)
        
        Returns:
            List[Dict[str, Any]: 테이블 데이터 리스트
        """
        if self.sheet_config.sheet_type != 'table':
            self.logger.error(f"Sheet {self.sheet_key} is not a table type")
            return []
        
        field_mapping = self.get_field_mapping()
        
        # 데이터 범위 계산
        start_col = min(field_mapping.values())
        end_col = max(field_mapping.values())
        start_row = self.sheet_config.row_start
        
        range_address = f"{start_col}{start_row}:{end_col}"
        
        # 데이터 조회
        raw_data = self.get_range_values(range_address)
        if not raw_data:
            return []
        
        # 데이터 변환
        result = []
        reverse_mapping = {v: k for k, v in field_mapping.items()}  # 셀 주소 -> 필드명
        
        for row in raw_data:
            if any(row):  # 빈 행이 아닌 경우
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(field_mapping):
                        # 컬럼 순서에 따른 필드명 찾기
                        column_letter = list(field_mapping.values())[i]
                        field_name = reverse_mapping.get(column_letter)
                        if field_name:
                            row_dict[field_name] = value
                
                if row_dict:
                    result.append(row_dict)
        
        return result
    
    def validate_structure(self) -> Dict[str, Any]:
        """
        시트 구조 검증
        
        Returns:
            Dict[str, Any]: 검증 결과
        """
        if self.sheet_config.sheet_type in ['config', 'table']:
            # 헤더 행 조회
            header_row = self.sheet_config.row_start
            if self.sheet_config.sheet_type == 'config':
                range_address = f"A{header_row}:Z{header_row}"
            else:  # table
                start_col = min(self.get_field_mapping().values())
                end_col = max(self.get_field_mapping().values())
                range_address = f"{start_col}{header_row}:{end_col}{header_row}"
            
            headers = self.get_range_values(range_address)
            if headers and len(headers) > 0:
                actual_headers = [str(h).strip() for h in headers[0] if h]
                return self.schema_loader.validate_sheet_structure(self.sheet_key, actual_headers)
        
        return {'valid': True, 'message': 'Structure validation not applicable'}
    
    def get_sheet_info(self) -> Dict[str, Any]:
        """
        시트 정보 조회
        
        Returns:
            Dict[str, Any]: 시트 정보
        """
        base_info = super().get_sheet_info()
        
        # 스키마 정보 추가
        base_info.update({
            'sheet_key': self.sheet_key,
            'sheet_type': self.sheet_config.sheet_type,
            'field_mapping': self.get_field_mapping(),
            'row_start': self.sheet_config.row_start
        })
        
        return base_info
    
    def _get_next_empty_row(self) -> int:
        """
        다음 빈 행 번호 계산
        
        Returns:
            int: 다음 빈 행 번호
        """
        if self.sheet_config.sheet_type != 'table':
            return self.sheet_config.row_start
        
        # 현재 데이터 조회
        current_data = self.get_table_data()
        if current_data:
            return len(current_data) + self.sheet_config.row_start
        else:
            return self.sheet_config.row_start
