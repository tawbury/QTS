#!/usr/bin/env python3
"""
Schema Loader 테스트
"""

import pytest
from pathlib import Path
from src.qts.core.config.schema_loader import get_schema_loader, SchemaLoader, SheetConfig, BlockConfig


class TestSchemaLoader:
    """SchemaLoader 테스트 클래스"""
    
    def setup_method(self):
        """테스트 설정"""
        self.project_root = Path('.')
        self.schema_loader = get_schema_loader(self.project_root)
    
    def test_load_schema_success(self):
        """스키마 로드 성공 테스트"""
        schema = self.schema_loader.load_schema()
        
        assert schema is not None
        assert "schema_version" in schema
        assert "sheets" in schema
        assert isinstance(schema["sheets"], dict)
    
    def test_get_sheet_config(self):
        """시트 설정 조회 테스트"""
        # Portfolio 시트 설정 조회
        portfolio_config = self.schema_loader.get_sheet_config('Portfolio')
        assert portfolio_config is not None
        assert portfolio_config.sheet_name == "Portfolio"
        assert portfolio_config.sheet_type == "dashboard"
        assert portfolio_config.blocks is not None
        
        # Performance 시트 설정 조회
        performance_config = self.schema_loader.get_sheet_config('Performance')
        assert performance_config is not None
        assert performance_config.sheet_name == "Performance"
        assert performance_config.sheet_type == "dashboard"
        assert performance_config.blocks is not None
        
        # 존재하지 않는 시트 조회
        nonexistent_config = self.schema_loader.get_sheet_config('NonExistent')
        assert nonexistent_config is None
    
    def test_get_block_config(self):
        """블록 설정 조회 테스트"""
        # Portfolio KPI 블록 조회
        kpi_block = self.schema_loader.get_block_config('Portfolio', 'kpi_overview')
        assert kpi_block is not None
        assert kpi_block.title_cell == "A1"
        assert kpi_block.merge_title == "A1:R1"
        assert kpi_block.body_range == "A2:R3"
        assert kpi_block.fields is not None
        
        # 존재하지 않는 블록 조회
        nonexistent_block = self.schema_loader.get_block_config('Portfolio', 'nonexistent')
        assert nonexistent_block is None
    
    def test_get_field_mapping(self):
        """필드 매핑 조회 테스트"""
        # Portfolio 필드 매핑
        portfolio_mapping = self.schema_loader.get_field_mapping('Portfolio')
        assert isinstance(portfolio_mapping, dict)
        assert len(portfolio_mapping) > 0
        
        # Performance 필드 매핑
        performance_mapping = self.schema_loader.get_field_mapping('Performance')
        assert isinstance(performance_mapping, dict)
        assert len(performance_mapping) > 0
        
        # Config 타입 필드 매핑
        config_mapping = self.schema_loader.get_field_mapping('config_scalp')
        assert isinstance(config_mapping, dict)
        assert len(config_mapping) > 0
    
    def test_get_all_sheet_configs(self):
        """모든 시트 설정 조회 테스트"""
        all_configs = self.schema_loader.get_all_sheet_configs()
        assert isinstance(all_configs, dict)
        assert len(all_configs) > 0
        
        # 필수 시트들 존재 확인
        required_sheets = ['Portfolio', 'Performance', 'Dividend', 'R_Dash']
        for sheet_name in required_sheets:
            assert sheet_name in all_configs
    
    def test_validate_sheet_structure(self):
        """시트 구조 검증 테스트"""
        # Config 타입 검증
        config_result = self.schema_loader.validate_sheet_structure('config_scalp', ['CATEGORY', 'SUB_CATEGORY', 'KEY', 'VALUE', 'DESCRIPTION', 'TAG'])
        assert 'valid' in config_result
        
        # Table 타입 검증
        table_result = self.schema_loader.validate_sheet_structure('T_Ledger', ['timestamp', 'symbol', 'market', 'side', 'qty', 'price'])
        assert 'valid' in table_result
        
        # Dashboard 타입 검증 (구조 검증 적용되지 않음)
        dashboard_result = self.schema_loader.validate_sheet_structure('Portfolio', [])
        assert dashboard_result['valid'] is True  # Dashboard 타입은 구조 검증 적용되지 않음


class TestSheetConfig:
    """SheetConfig 데이터클래스 테스트"""
    
    def test_sheet_config_creation(self):
        """SheetConfig 생성 테스트"""
        config = SheetConfig(
            sheet_name="TestSheet",
            sheet_type="table",
            row_start=2,
            columns={"field1": "A", "field2": "B"}
        )
        
        assert config.sheet_name == "TestSheet"
        assert config.sheet_type == "table"
        assert config.row_start == 2
        assert config.columns == {"field1": "A", "field2": "B"}
        assert config.fields is None
        assert config.blocks is None


class TestBlockConfig:
    """BlockConfig 데이터클래스 테스트"""
    
    def test_block_config_creation(self):
        """BlockConfig 생성 테스트"""
        config = BlockConfig(
            title_cell="A1",
            merge_title="A1:E1",
            body_range="A2:E5",
            fields={"field1": "A3", "field2": "B3"}
        )
        
        assert config.title_cell == "A1"
        assert config.merge_title == "A1:E1"
        assert config.body_range == "A2:E5"
        assert config.fields == {"field1": "A3", "field2": "B3"}


if __name__ == "__main__":
    pytest.main([__file__])
