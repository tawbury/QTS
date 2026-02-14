#!/usr/bin/env python3
"""
Repository Manager 테스트
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.db.repository_manager import RepositoryManager


class TestRepositoryManager:
    """RepositoryManager 테스트 클래스"""
    
    def setup_method(self):
        """테스트 설정"""
        self.mock_client = Mock()
        self.mock_client.spreadsheet_id = "test_spreadsheet_id"
        self.manager = RepositoryManager(self.mock_client)
    
    def test_initialization(self):
        """초리화 테스트"""
        assert self.manager.client == self.mock_client
        assert hasattr(self.manager, 'repositories')
        assert hasattr(self.manager, 'repository_classes')
    
    def test_register_repository(self):
        """리포지토리 클래스 등록 테스트"""
        # Mock 리포지토리 클래스 생성
        mock_repo_class = Mock()
        mock_repo_class.__name__ = "MockRepositoryClass"
        
        self.manager.register_repository('test_sheet', mock_repo_class)
        
        assert 'test_sheet' in self.manager.repository_classes
        assert self.manager.repository_classes['test_sheet'] == mock_repo_class
    
    @pytest.mark.asyncio
    async def test_get_repository(self):
        """리포지토리 인스턴스 조회 테스트"""
        mock_repo_class = Mock()
        mock_repo_class.__name__ = "MockRepositoryClass"
        mock_repo_instance = Mock()
        mock_repo_class.return_value = mock_repo_instance
        
        self.manager.register_repository('test_sheet', mock_repo_class)
        
        # 리포지토리 인스턴스 조회
        repository = await self.manager.get_repository('test_sheet')
        assert repository == mock_repo_instance
        
        # 존재하지 않는 리포지토리 조회
        with pytest.raises(ValueError, match="No repository class registered"):
            await self.manager.get_repository('nonexistent')
    
    @pytest.mark.asyncio
    async def test_create_repository(self):
        """리포지토리 인스턴스 생성 테스트"""
        mock_repo_class = Mock()
        mock_repo_class.__name__ = "MockRepositoryClass"
        mock_repo_instance = Mock()
        mock_repo_class.return_value = mock_repo_instance
        
        # 리포지토리 생성
        repository = await self.manager.create_repository('test_sheet', mock_repo_class)
        assert repository == mock_repo_instance
        assert 'test_sheet' in self.manager.repository_classes
        assert 'test_sheet' in self.manager.repositories
    
    @pytest.mark.asyncio
    async def test_get_all_repositories(self):
        """모든 리포지토리 인스턴스 조회 테스트"""
        # Mock 리포지토리 인스턴스 추가
        mock_repo1 = Mock()
        mock_repo2 = Mock()
        self.manager.repositories['sheet1'] = mock_repo1
        self.manager.repositories['sheet2'] = mock_repo2
        
        all_repos = await self.manager.get_all_repositories()
        assert len(all_repos) == 2
        assert 'sheet1' in all_repos
        assert 'sheet2' in all_repos
        assert all_repos['sheet1'] == mock_repo1
        assert all_repos['sheet2'] == mock_repo2
    
    @pytest.mark.asyncio
    async def test_clear_repository_cache(self):
        """리포지토리 캐시 초기화 테스트"""
        mock_repo = Mock()
        mock_repo.clear_cache = AsyncMock()
        self.manager.repositories['test_sheet'] = mock_repo
        
        # 특정 리포지토리 캐시 초기화
        await self.manager.clear_repository_cache('test_sheet')
        mock_repo.clear_cache.assert_called_once()
        
        # 전체 캐시 초기화
        mock_repo.clear_cache.reset_mock()
        await self.manager.clear_repository_cache()
        mock_repo.clear_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """헬스체크 테스트"""
        self.mock_client.health_check = AsyncMock(return_value={'status': 'healthy'})
        
        health = await self.manager.health_check()
        assert health['status'] == 'healthy'
        self.mock_client.health_check.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
