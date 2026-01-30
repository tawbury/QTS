"""
Schema Loader

스키마 파일을 로드하고 시트 구조를 관리합니다.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class SheetConfig:
    """시트 설정 정보"""
    sheet_name: str
    sheet_type: str  # 'config', 'table', 'dashboard'
    row_start: int = 2
    fields: Optional[Dict[str, Any]] = None
    columns: Optional[Dict[str, str]] = None
    blocks: Optional[Dict[str, Any]] = None


@dataclass
class BlockConfig:
    """블록 설정 정보"""
    title_cell: str
    merge_title: Optional[str] = None
    body_range: Optional[str] = None
    fields: Optional[Dict[str, str]] = None


class SchemaLoader:
    """스키마 로더"""
    
    def __init__(self, project_root: Path):
        """
        SchemaLoader 초기화
        
        Args:
            project_root: 프로젝트 루트 경로
        """
        self.project_root = project_root
        self.schema_path = project_root / "config" / "schema" / "credentials.json"
        self.logger = logging.getLogger(__name__)
        
        # 캐싱
        self._schema_cache = None
        self._sheet_configs_cache = None
    
    def load_schema(self) -> Dict[str, Any]:
        """
        스키마 파일 로드
        
        Returns:
            Dict[str, Any]: 스키마 데이터
        """
        if self._schema_cache is not None:
            return self._schema_cache
        
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            self._schema_cache = schema
            self.logger.info(f"Schema loaded from {self.schema_path}")
            return schema
            
        except Exception as e:
            self.logger.error(f"Failed to load schema: {str(e)}")
            return {}
    
    def get_sheet_config(self, sheet_key: str) -> Optional[SheetConfig]:
        """
        시트 설정 조회
        
        Args:
            sheet_key: 시트 키 (예: 'Portfolio', 'Performance')
            
        Returns:
            Optional[SheetConfig]: 시트 설정 정보
        """
        if self._sheet_configs_cache is None:
            self._build_sheet_configs_cache()
        
        return self._sheet_configs_cache.get(sheet_key)
    
    def _build_sheet_configs_cache(self) -> None:
        """시트 설정 캐시 빌드"""
        self._sheet_configs_cache = {}
        schema = self.load_schema()
        
        sheets = schema.get('sheets', {})
        
        for sheet_key, sheet_data in sheets.items():
            sheet_name = sheet_data.get('sheet_name')
            
            # 시트 타입 결정
            if 'fields' in sheet_data:
                sheet_type = 'config'
            elif 'columns' in sheet_data:
                sheet_type = 'table'
            elif 'blocks' in sheet_data:
                sheet_type = 'dashboard'
            else:
                sheet_type = 'unknown'
            
            config = SheetConfig(
                sheet_name=sheet_name,
                sheet_type=sheet_type,
                row_start=sheet_data.get('row_start', 2),
                fields=sheet_data.get('fields'),
                columns=sheet_data.get('columns'),
                blocks=sheet_data.get('blocks')
            )
            
            self._sheet_configs_cache[sheet_key] = config
    
    def get_block_config(self, sheet_key: str, block_name: str) -> Optional[BlockConfig]:
        """
        블록 설정 조회
        
        Args:
            sheet_key: 시트 키
            block_name: 블록 이름
            
        Returns:
            Optional[BlockConfig]: 블록 설정 정보
        """
        sheet_config = self.get_sheet_config(sheet_key)
        if not sheet_config or not sheet_config.blocks:
            return None
        
        block_data = sheet_config.blocks.get(block_name)
        if not block_data:
            return None
        
        return BlockConfig(
            title_cell=block_data.get('title_cell'),
            merge_title=block_data.get('merge_title'),
            body_range=block_data.get('body_range'),
            fields=block_data.get('fields')
        )
    
    def get_field_mapping(self, sheet_key: str) -> Dict[str, str]:
        """
        필드 매핑 정보 조회
        
        Args:
            sheet_key: 시트 키
            
        Returns:
            Dict[str, str]: 필드명 -> 셀 주소 매핑
        """
        sheet_config = self.get_sheet_config(sheet_key)
        if not sheet_config:
            return {}
        
        mapping = {}
        
        if sheet_config.sheet_type == 'config':
            # Config 타입: header_key 기반 매핑
            for field_name, field_config in sheet_config.fields.items():
                header_key = field_config.get('header_key')
                if header_key:
                    mapping[field_name] = header_key
        
        elif sheet_config.sheet_type == 'table':
            # Table 타입: 컬럼 기반 매핑
            for field_name, column in sheet_config.columns.items():
                mapping[field_name] = column
        
        elif sheet_config.sheet_type == 'dashboard':
            # Dashboard 타입: 블록 필드 기반 매핑
            if sheet_config.blocks:
                for block_name, block_data in sheet_config.blocks.items():
                    fields = block_data.get('fields', {})
                    for field_name, cell_address in fields.items():
                        mapping[f"{block_name}_{field_name}"] = cell_address
        
        return mapping
    
    def get_all_sheet_configs(self) -> Dict[str, SheetConfig]:
        """
        모든 시트 설정 조회
        
        Returns:
            Dict[str, SheetConfig]: 모든 시트 설정
        """
        if self._sheet_configs_cache is None:
            self._build_sheet_configs_cache()
        
        return self._sheet_configs_cache.copy()
    
    def validate_sheet_structure(self, sheet_key: str, actual_headers: List[str]) -> Dict[str, Any]:
        """
        시트 구조 검증
        
        Args:
            sheet_key: 시트 키
            actual_headers: 실제 헤더 리스트
            
        Returns:
            Dict[str, Any]: 검증 결과
        """
        sheet_config = self.get_sheet_config(sheet_key)
        if not sheet_config:
            return {
                'valid': False,
                'error': f'Sheet config not found for {sheet_key}'
            }
        
        expected_fields = []
        
        if sheet_config.sheet_type == 'config':
            expected_fields = [
                field.get('header_key') 
                for field in sheet_config.fields.values()
                if field.get('header_key')
            ]
        
        elif sheet_config.sheet_type == 'table':
            expected_fields = list(sheet_config.columns.values())
        
        # 필드 검증
        missing_fields = set(expected_fields) - set(actual_headers)
        extra_fields = set(actual_headers) - set(expected_fields)
        
        return {
            'valid': len(missing_fields) == 0,
            'expected_fields': expected_fields,
            'actual_fields': actual_headers,
            'missing_fields': list(missing_fields),
            'extra_fields': list(extra_fields)
        }


# 전역 인스턴스
_schema_loader_instance = None

def get_schema_loader(project_root: Path) -> SchemaLoader:
    """
    SchemaLoader 인스턴스 가져오기
    
    Args:
        project_root: 프로젝트 루트 경로
        
    Returns:
        SchemaLoader: SchemaLoader 인스턴스
    """
    global _schema_loader_instance
    
    if _schema_loader_instance is None:
        _schema_loader_instance = SchemaLoader(project_root)
    
    return _schema_loader_instance
