"""
리포지토리 매니저

QTS 시스템의 모든 리포지토리를 관리하는 매니저 클래스입니다.
리포지토리 팩토리, 연결 풀 관리, 트랜잭션 관리 기능을 제공합니다.
"""

from typing import Dict, Any, Optional, Type
import logging
from datetime import datetime

from .google_sheets_client import GoogleSheetsClient, get_google_sheets_client
from .repositories.base_repository import BaseSheetRepository
from .mappers.field_mapper import FieldMapper


class RepositoryManager:
    """
    리포지토리 매니저
    
    모든 시트 리포지토리의 생성, 관리, 연결을 담당합니다.
    """
    
    def __init__(self, client: Optional[GoogleSheetsClient] = None):
        """
        RepositoryManager 초기화
        
        Args:
            client: Google Sheets 클라이언트 (선택사항)
        """
        self.client = client
        self.repositories: Dict[str, BaseSheetRepository] = {}
        self.field_mapper = FieldMapper()
        self.logger = logging.getLogger(__name__)
        
        # 리포지토리 클래스 레지스트리
        self.repository_classes: Dict[str, Type[BaseSheetRepository]] = {}
        
        self.logger.info("RepositoryManager initialized")
    
    async def initialize(self):
        """리포지토리 매니저 초기화"""
        if not self.client:
            self.client = await get_google_sheets_client()
        
        self.logger.info("RepositoryManager initialized with Google Sheets client")
    
    def register_repository(self, sheet_name: str, repository_class: Type[BaseSheetRepository]):
        """
        리포지토리 클래스 등록
        
        Args:
            sheet_name: 시트 이름
            repository_class: 리포지토리 클래스
        """
        self.repository_classes[sheet_name] = repository_class
        self.logger.info(f"Registered repository class for sheet '{sheet_name}': {repository_class.__name__}")
    
    async def get_repository(self, sheet_name: str) -> BaseSheetRepository:
        """
        리포지토리 인스턴스获取
        
        Args:
            sheet_name: 시트 이름
            
        Returns:
            BaseSheetRepository: 리포지토리 인스턴스
            
        Raises:
            ValueError: 리포지토리 클래스가 등록되지 않은 경우
        """
        if sheet_name not in self.repositories:
            if sheet_name not in self.repository_classes:
                raise ValueError(f"No repository class registered for sheet '{sheet_name}'")
            
            repository_class = self.repository_classes[sheet_name]
            
            # 리포지토리 인스턴스 생성
            repository = repository_class(
                client=self.client,
                spreadsheet_id=self.client.spreadsheet_id,
                sheet_name=sheet_name
            )
            
            self.repositories[sheet_name] = repository
            self.logger.info(f"Created repository instance for sheet '{sheet_name}'")
        
        return self.repositories[sheet_name]
    
    async def create_repository(
        self, 
        sheet_name: str, 
        repository_class: Type[BaseSheetRepository]
    ) -> BaseSheetRepository:
        """
        리포지토리 인스턴스 생성
        
        Args:
            sheet_name: 시트 이름
            repository_class: 리포지토리 클래스
            
        Returns:
            BaseSheetRepository: 생성된 리포지토리 인스턴스
        """
        # 클래스 등록
        self.register_repository(sheet_name, repository_class)
        
        # 인스턴스 생성 및 반환
        return await self.get_repository(sheet_name)
    
    async def get_all_repositories(self) -> Dict[str, BaseSheetRepository]:
        """
        모든 리포지토리 인스턴스获取
        
        Returns:
            Dict[str, BaseSheetRepository]: 모든 리포지토리
        """
        return self.repositories.copy()
    
    async def clear_repository_cache(self, sheet_name: Optional[str] = None):
        """
        리포지토리 캐시 초기화
        
        Args:
            sheet_name: 초기화할 시트 이름 (None이면 전체)
        """
        if sheet_name:
            if sheet_name in self.repositories:
                repository = self.repositories[sheet_name]
                if hasattr(repository, 'clear_cache'):
                    await repository.clear_cache()
                self.logger.info(f"Cleared cache for repository '{sheet_name}'")
        else:
            for name, repository in self.repositories.items():
                if hasattr(repository, 'clear_cache'):
                    await repository.clear_cache()
            self.logger.info("Cleared cache for all repositories")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        리포지토리 매니저 헬스체크
        
        Returns:
            Dict[str, Any]: 헬스체크 결과
        """
        try:
            # 클라이언트 헬스체크
            client_health = await self.client.health_check()
            
            # 모든 리포지토리 헬스체크
            repository_health = {}
            for sheet_name, repository in self.repositories.items():
                try:
                    repo_health = await repository.health_check()
                    repository_health[sheet_name] = repo_health
                except Exception as e:
                    repository_health[sheet_name] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
            
            # 전체 상태 계산
            all_healthy = (
                client_health.get('status') == 'healthy' and
                all(repo.get('status') == 'healthy' for repo in repository_health.values())
            )
            
            return {
                'status': 'healthy' if all_healthy else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'client': client_health,
                'repositories': repository_health,
                'registered_classes': list(self.repository_classes.keys()),
                'active_instances': list(self.repositories.keys())
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def get_repository_stats(self) -> Dict[str, Any]:
        """
        리포지토리 통계 정보
        
        Returns:
            Dict[str, Any]: 통계 정보
        """
        try:
            stats = {
                'total_repositories': len(self.repositories),
                'registered_classes': len(self.repository_classes),
                'repositories': {}
            }
            
            for sheet_name, repository in self.repositories.items():
                try:
                    record_count = await repository.count_records()
                    sheet_info = await repository.get_sheet_info()
                    
                    stats['repositories'][sheet_name] = {
                        'class_name': repository.__class__.__name__,
                        'record_count': record_count,
                        'sheet_info': sheet_info
                    }
                except Exception as e:
                    stats['repositories'][sheet_name] = {
                        'error': str(e)
                    }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get repository stats: {str(e)}")
            return {'error': str(e)}
    
    async def close(self):
        """리포지토리 매니저 리소스 정리"""
        try:
            # 모든 리포지토리 캐시 정리
            await self.clear_repository_cache()
            
            # 리포지토리 인스턴스 정리
            self.repositories.clear()
            
            # 클라이언트 정리
            if self.client:
                # 클라이언트는 전역 인스턴스이므로 여기서 정리하지 않음
                pass
            
            self.logger.info("RepositoryManager closed")
            
        except Exception as e:
            self.logger.error(f"Error closing RepositoryManager: {str(e)}")


# 전역 리포지토리 매니저 인스턴스
_repository_manager: Optional[RepositoryManager] = None


async def get_repository_manager() -> RepositoryManager:
    """
    전역 리포지토리 매니저 인스턴스获取
    
    Returns:
        RepositoryManager: 리포지토리 매니저 인스턴스
    """
    global _repository_manager
    
    if _repository_manager is None:
        _repository_manager = RepositoryManager()
        await _repository_manager.initialize()
    
    return _repository_manager


async def close_repository_manager():
    """전역 리포지토리 매니저 리소스 정리"""
    global _repository_manager
    
    if _repository_manager:
        await _repository_manager.close()
        _repository_manager = None
