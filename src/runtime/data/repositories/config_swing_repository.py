"""
Config_Swing 리포지토리

스윙 트레이딩 설정(Config_Swing) 시트의 데이터를 관리하는 리포지토리입니다.
스윙 전략의 설정 파라미터를 관리합니다.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .base_repository import BaseSheetRepository
from ..google_sheets_client import ValidationError


class ConfigSwingRepository(BaseSheetRepository):
    """
    Config_Swing 리포지토리
    
    스윙 트레이딩 설정 데이터를 관리하는 리포지토리 클래스입니다.
    """
    
    def __init__(self, client, spreadsheet_id: str):
        """
        ConfigSwingRepository 초기화
        
        Args:
            client: Google Sheets 클라이언트
            spreadsheet_id: 스프레드시트 ID
        """
        super().__init__(client, spreadsheet_id, "Config_Swing")
        
        # 필수 필드 정의
        self.required_fields = [
            'CATEGORY', 'SUB_CATEGORY', 'KEY', 'VALUE', 'DESCRIPTION'
        ]
        
        self.logger.info(f"ConfigSwingRepository initialized for sheet '{self.sheet_name}'")
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """모든 스윙 설정 조회"""
        try:
            headers = await self.get_headers()
            if not headers:
                return []
            
            # 헤더 다음 행부터 모든 데이터 조회
            range_name = f"{self.sheet_name}!A{self.header_row + 1}:Z"
            raw_data = await self.client.get_sheet_data(range_name)
            
            result = []
            for row in raw_data:
                if row and any(cell.strip() for cell in row):  # 빈 행 제외
                    record = self._row_to_dict(row, headers)
                    result.append(record)
            
            self.logger.info(f"Retrieved {len(result)} swing config records")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get all swing config: {str(e)}")
            raise
    
    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 설정 조회
        
        Args:
            record_id: 설정 ID (KEY 기반)
            
        Returns:
            Optional[Dict[str, Any]]: 설정 정보 또는 None
        """
        try:
            all_configs = await self.get_all()
            
            for config in all_configs:
                if config.get('KEY', '').upper() == record_id.upper():
                    return config
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get swing config by ID '{record_id}': {str(e)}")
            raise
    
    async def get_config_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        카테고리로 설정 조회
        
        Args:
            category: 카테고리 이름
            
        Returns:
            List[Dict[str, Any]]: 카테고리별 설정 리스트
        """
        try:
            all_configs = await self.get_all()
            category_configs = []
            
            for config in all_configs:
                if config.get('CATEGORY', '').upper() == category.upper():
                    category_configs.append(config)
            
            self.logger.info(f"Found {len(category_configs)} configs for category '{category}'")
            return category_configs
            
        except Exception as e:
            self.logger.error(f"Failed to get configs by category '{category}': {str(e)}")
            raise
    
    async def get_config_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """
        키로 설정 조회
        
        Args:
            key: 설정 키
            
        Returns:
            Optional[Dict[str, Any]]: 설정 정보 또는 None
        """
        return await self.get_by_id(key)
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        새 설정 생성
        
        Args:
            data: 설정 데이터
            
        Returns:
            Dict[str, Any]: 생성된 설정
        """
        try:
            # 필수 필드 검증
            self._validate_required_fields(data, self.required_fields)
            
            # 데이터 정제
            sanitized_data = self._sanitize_data(data)
            
            # 시트에 추가
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized_data, headers)
            
            range_name = f"{self.sheet_name}!A:Z"
            await self.client.append_sheet_data(range_name, [row_data])
            
            self.logger.info(f"Created new swing config: {sanitized_data.get('KEY')}")
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Failed to create swing config: {str(e)}")
            raise
    
    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        설정 업데이트
        
        Args:
            record_id: 설정 ID (KEY)
            data: 업데이트할 데이터
            
        Returns:
            Dict[str, Any]: 업데이트된 설정
        """
        try:
            # 기존 데이터 조회
            existing_record = await self.get_by_id(record_id)
            if not existing_record:
                raise ValueError(f"Swing config with key '{record_id}' not found")
            
            # 데이터 병합
            updated_data = {**existing_record, **data}
            
            # 데이터 정제
            sanitized_data = self._sanitize_data(updated_data)
            
            # 행 번호 찾기
            row_number = await self._find_row_by_id(record_id, 'KEY')
            if not row_number:
                raise ValueError(f"Could not find row for config key '{record_id}'")
            
            # 시트 업데이트
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized_data, headers)
            
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [row_data])
            
            self.logger.info(f"Updated swing config: {record_id}")
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Failed to update swing config '{record_id}': {str(e)}")
            raise
    
    async def update_config(
        self,
        key: str,
        value: Any,
        description: str = None,
        tag: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        설정 업데이트 (편의 메서드)
        
        Args:
            key: 설정 키
            value: 설정 값
            description: 설명
            tag: 태그
            **kwargs: 추가 필드
            
        Returns:
            Dict[str, Any]: 업데이트된 설정
        """
        update_data = {'VALUE': value}
        
        if description is not None:
            update_data['DESCRIPTION'] = description
        if tag is not None:
            update_data['TAG'] = tag
        
        update_data.update(kwargs)
        
        return await self.update(key, update_data)
    
    async def delete(self, record_id: str) -> bool:
        """
        설정 삭제
        
        Args:
            record_id: 설정 ID (KEY)
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 행 번호 찾기
            row_number = await self._find_row_by_id(record_id, 'KEY')
            if not row_number:
                return False
            
            # 행 삭제 (빈 값으로 업데이트)
            headers = await self.get_headers()
            empty_row = [''] * len(headers)
            
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [empty_row])
            
            self.logger.info(f"Deleted swing config: {record_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete swing config '{record_id}': {str(e)}")
            raise
    
    async def exists(self, record_id: str) -> bool:
        """
        설정 존재 여부 확인
        
        Args:
            record_id: 설정 ID (KEY)
            
        Returns:
            bool: 존재 여부
        """
        try:
            existing_record = await self.get_by_id(record_id)
            return existing_record is not None
        except Exception as e:
            self.logger.error(f"Failed to check swing config existence '{record_id}': {str(e)}")
            return False
    
    async def get_config_value(self, key: str, default_value: Any = None) -> Any:
        """
        설정 값 조회 (편의 메서드)
        
        Args:
            key: 설정 키
            default_value: 기본값
            
        Returns:
            Any: 설정 값 또는 기본값
        """
        try:
            config = await self.get_by_key(key)
            if config:
                return config.get('VALUE', default_value)
            return default_value
        except Exception as e:
            self.logger.error(f"Failed to get config value '{key}': {str(e)}")
            return default_value
    
    async def get_market_filters(self) -> Dict[str, Any]:
        """
        시장 필터 설정 조회
        
        Returns:
            Dict[str, Any]: 시장 필터 설정
        """
        try:
            market_configs = await self.get_config_by_category('MARKET_FILTERS')
            
            filters = {}
            for config in market_configs:
                key = config.get('KEY', '')
                value = config.get('VALUE', '')
                
                if key and value:
                    # 불리언 값 변환
                    if value.upper() in ['TRUE', 'FALSE']:
                        filters[key] = value.upper() == 'TRUE'
                    else:
                        filters[key] = value
            
            self.logger.info(f"Retrieved {len(filters)} market filter configs")
            return filters
            
        except Exception as e:
            self.logger.error(f"Failed to get market filters: {str(e)}")
            raise
    
    async def get_strategy_parameters(self) -> Dict[str, Any]:
        """
        전략 파라미터 설정 조회
        
        Returns:
            Dict[str, Any]: 전략 파라미터 설정
        """
        try:
            strategy_configs = await self.get_config_by_category('STRATEGY_PARAMETERS')
            
            parameters = {}
            for config in strategy_configs:
                key = config.get('KEY', '')
                value = config.get('VALUE', '')
                
                if key and value:
                    # 숫자 값 변환 시도
                    try:
                        if '.' in value:
                            parameters[key] = float(value)
                        else:
                            parameters[key] = int(value)
                    except ValueError:
                        # 불리언 값 변환 시도
                        if value.upper() in ['TRUE', 'FALSE']:
                            parameters[key] = value.upper() == 'TRUE'
                        else:
                            parameters[key] = value
            
            self.logger.info(f"Retrieved {len(parameters)} strategy parameter configs")
            return parameters
            
        except Exception as e:
            self.logger.error(f"Failed to get strategy parameters: {str(e)}")
            raise
    
    async def get_risk_management(self) -> Dict[str, Any]:
        """
        리스크 관리 설정 조회
        
        Returns:
            Dict[str, Any]: 리스크 관리 설정
        """
        try:
            risk_configs = await self.get_config_by_category('RISK_MANAGEMENT')
            
            risk_settings = {}
            for config in risk_configs:
                key = config.get('KEY', '')
                value = config.get('VALUE', '')
                
                if key and value:
                    # 숫자 값 변환 시도
                    try:
                        if '.' in value:
                            risk_settings[key] = float(value)
                        else:
                            risk_settings[key] = int(value)
                    except ValueError:
                        # 불리언 값 변환 시도
                        if value.upper() in ['TRUE', 'FALSE']:
                            risk_settings[key] = value.upper() == 'TRUE'
                        else:
                            risk_settings[key] = value
            
            self.logger.info(f"Retrieved {len(risk_settings)} risk management configs")
            return risk_settings
            
        except Exception as e:
            self.logger.error(f"Failed to get risk management settings: {str(e)}")
            raise
    
    async def get_config_summary(self) -> Dict[str, Any]:
        """
        설정 요약 정보 조회
        
        Returns:
            Dict[str, Any]: 설정 요약
        """
        try:
            all_configs = await self.get_all()
            
            # 카테고리별 그룹화
            categories = {}
            for config in all_configs:
                category = config.get('CATEGORY', 'UNKNOWN')
                if category not in categories:
                    categories[category] = []
                categories[category].append(config)
            
            # 태그별 그룹화
            tags = {}
            for config in all_configs:
                tag = config.get('TAG', 'UNTAGGED')
                if tag not in tags:
                    tags[tag] = []
                tags[tag].append(config)
            
            summary = {
                'total_configs': len(all_configs),
                'categories': {cat: len(configs) for cat, configs in categories.items()},
                'tags': {tag: len(configs) for tag, configs in tags.items()},
                'category_details': categories,
                'last_updated': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get config summary: {str(e)}")
            raise
