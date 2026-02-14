#!/usr/bin/env python3
"""
Base Repository 테스트
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.db.repositories.base_repository import BaseSheetRepository


class TestBaseSheetRepository:
    """BaseSheetRepository 테스트 클래스"""
    
    def test_abstract_methods(self):
        """추상 메서드 존재 확인"""
        abstract_methods = BaseSheetRepository.__abstractmethods__
        expected_methods = {
            'get_all', 'get_by_id', 'create', 'update', 'delete', 'exists'
        }
        
        assert abstract_methods == expected_methods, \
            f"Expected abstract methods {expected_methods}, got {abstract_methods}"
    
    def test_initialization(self):
        """초기화 테스트"""
        # Mock client 생성
        mock_client = Mock()
        spreadsheet_id = "test_spreadsheet_id"
        sheet_name = "test_sheet"
        
        # 추상 클래스이므로 직접 인스턴스화 불가
        # 하지만 초기화 로직 검증을 위한 서브클래스 생성
        class TestRepository(BaseSheetRepository):
            async def get_all(self):
                return []
            
            async def get_by_id(self, record_id):
                return None
            
            async def create(self, data):
                return data
            
            async def update(self, record_id, data):
                return data
            
            async def delete(self, record_id):
                return True
            
            async def exists(self, record_id):
                return False
        
        # 서브클래스로 초기화 테스트
        repo = TestRepository(mock_client, spreadsheet_id, sheet_name)
        
        assert repo.client == mock_client
        assert repo.spreadsheet_id == spreadsheet_id
        assert repo.sheet_name == sheet_name
        assert repo.header_row == 1
        assert repo.range_name == f"{sheet_name}!A:Z"


if __name__ == "__main__":
    pytest.main([__file__])
