"""
R_Dash 리포지토리

리스크 대시보드(R_Dash) 시트의 데이터를 관리하는 리포지토리입니다.
리스크 관련 대시보드 데이터를 관리합니다.
"""

from typing import List, Dict, Any, Optional

from .base_repository import BaseSheetRepository
from ...shared.timezone_utils import now_kst


class R_DashRepository(BaseSheetRepository):
    """
    R_Dash 리포지토리
    
    리스크 대시보드 데이터를 관리하는 리포지토리 클래스입니다.
    """
    
    def __init__(self, client, spreadsheet_id: str):
        """
        R_DashRepository 초기화
        
        Args:
            client: Google Sheets 클라이언트
            spreadsheet_id: 스프레드시트 ID
        """
        super().__init__(client, spreadsheet_id, "R_Dash")
        
        # 필수 필드 정의 (R_Dash는 구조가 다를 수 있음)
        self.required_fields = ['GLOBAL_RISK_PANEL']
        
        self.logger.info(f"R_DashRepository initialized for sheet '{self.sheet_name}'")
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """모든 대시보드 데이터 조회"""
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
            
            self.logger.info(f"Retrieved {len(result)} dashboard records")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get all dashboard data: {str(e)}")
            raise
    
    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 대시보드 데이터 조회
        
        Args:
            record_id: 대시보드 데이터 ID (첫 번째 컬럼 기반)
            
        Returns:
            Optional[Dict[str, Any]]: 대시보드 데이터 또는 None
        """
        try:
            all_data = await self.get_all()
            
            for record in all_data:
                # 첫 번째 컬럼(ID)로 조회
                first_col_value = list(record.values())[0] if record else ''
                if str(first_col_value) == str(record_id):
                    return record
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get dashboard data by ID '{record_id}': {str(e)}")
            raise
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """
        대시보드 데이터 조회
        
        Returns:
            Dict[str, Any]: 대시보드 데이터
        """
        try:
            all_data = await self.get_all()
            
            # 대시보드 데이터 구조화
            dashboard_data = {
                'risk_panel': {},
                'metrics': {},
                'alerts': [],
                'last_updated': now_kst().isoformat()
            }
            
            for record in all_data:
                if not record:
                    continue
                
                # 첫 번째 컬럼을 키로 사용
                first_col = list(record.keys())[0] if record else ''
                first_val = record.get(first_col, '')
                
                if first_val:
                    # 리스크 패널 데이터
                    if 'RISK' in first_val.upper() or 'PANEL' in first_val.upper():
                        dashboard_data['risk_panel'][first_val] = record
                    
                    # 메트릭 데이터
                    elif any(metric in first_val.upper() for metric in ['LEVEL', 'CAP', 'MDD', 'STATE']):
                        dashboard_data['metrics'][first_val] = record
                    
                    # 알림 데이터
                    elif any(alert in first_val.upper() for alert in ['ALERT', 'WARNING', 'CRITICAL']):
                        dashboard_data['alerts'].append(record)
            
            self.logger.info("Retrieved dashboard data")
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {str(e)}")
            raise
    
    async def get_widget_data(self, widget_name: str) -> Optional[Dict[str, Any]]:
        """
        위젯 데이터 조회
        
        Args:
            widget_name: 위젯 이름
            
        Returns:
            Optional[Dict[str, Any]]: 위젯 데이터 또는 None
        """
        try:
            all_data = await self.get_all()
            
            for record in all_data:
                if record:
                    # 첫 번째 컬럼이 위젯 이름과 일치하는지 확인
                    first_col_value = list(record.values())[0] if record else ''
                    if str(first_col_value).upper() == str(widget_name).upper():
                        return record
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get widget data '{widget_name}': {str(e)}")
            raise
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        새 대시보드 데이터 생성
        
        Args:
            data: 대시보드 데이터
            
        Returns:
            Dict[str, Any]: 생성된 대시보드 데이터
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
            
            self.logger.info("Created new dashboard record")
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Failed to create dashboard record: {str(e)}")
            raise
    
    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        대시보드 데이터 업데이트
        
        Args:
            record_id: 대시보드 데이터 ID (첫 번째 컬럼)
            data: 업데이트할 데이터
            
        Returns:
            Dict[str, Any]: 업데이트된 대시보드 데이터
        """
        try:
            # 기존 데이터 조회
            existing_record = await self.get_by_id(record_id)
            if not existing_record:
                raise ValueError(f"Dashboard record with ID '{record_id}' not found")
            
            # 데이터 병합
            updated_data = {**existing_record, **data}
            
            # 데이터 정제
            sanitized_data = self._sanitize_data(updated_data)
            
            # 행 번호 찾기
            row_number = await self._find_row_by_id(record_id)
            if not row_number:
                raise ValueError(f"Could not find row for dashboard record '{record_id}'")
            
            # 시트 업데이트
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized_data, headers)
            
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [row_data])
            
            self.logger.info(f"Updated dashboard record: {record_id}")
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Failed to update dashboard record '{record_id}': {str(e)}")
            raise
    
    async def update_dashboard_widget(
        self,
        widget_name: str,
        values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        대시보드 위젯 업데이트 (편의 메서드)
        
        Args:
            widget_name: 위젯 이름
            values: 업데이트할 값들
            
        Returns:
            Dict[str, Any]: 업데이트된 위젯 데이터
        """
        # 기존 위젯 데이터 조회
        existing_widget = await self.get_widget_data(widget_name)
        
        if existing_widget:
            # 기존 위젯 업데이트
            return await self.update(widget_name, values)
        else:
            # 새 위젯 생성
            widget_data = {widget_name: None}
            widget_data.update(values)
            return await self.create(widget_data)
    
    async def delete(self, record_id: str) -> bool:
        """
        대시보드 데이터 삭제
        
        Args:
            record_id: 대시보드 데이터 ID (첫 번째 컬럼)
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 행 번호 찾기
            row_number = await self._find_row_by_id(record_id)
            if not row_number:
                return False
            
            # 행 삭제 (빈 값으로 업데이트)
            headers = await self.get_headers()
            empty_row = [''] * len(headers)
            
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [empty_row])
            
            self.logger.info(f"Deleted dashboard record: {record_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete dashboard record '{record_id}': {str(e)}")
            raise
    
    async def exists(self, record_id: str) -> bool:
        """
        대시보드 데이터 존재 여부 확인
        
        Args:
            record_id: 대시보드 데이터 ID (첫 번째 컬럼)
            
        Returns:
            bool: 존재 여부
        """
        try:
            existing_record = await self.get_by_id(record_id)
            return existing_record is not None
        except Exception as e:
            self.logger.error(f"Failed to check dashboard existence '{record_id}': {str(e)}")
            return False
    
    async def get_risk_status(self) -> Dict[str, Any]:
        """
        리스크 상태 조회
        
        Returns:
            Dict[str, Any]: 리스크 상태 정보
        """
        try:
            dashboard_data = await self.get_dashboard_data()
            
            risk_status = {
                'overall_status': 'UNKNOWN',
                'kill_switch_state': 'UNKNOWN',
                'exposure_level': 0,
                'daily_loss_cap': 0,
                'portfolio_mdd': 0,
                'final_risk_level': 'UNKNOWN',
                'alerts_count': len(dashboard_data.get('alerts', [])),
                'last_updated': dashboard_data.get('last_updated')
            }
            
            # 리스크 패널 데이터에서 상태 추출
            metrics = dashboard_data.get('metrics', {})
            
            for key, value in metrics.items():
                key_upper = key.upper()
                
                if 'KILLSWITCH' in key_upper and 'STATE' in key_upper:
                    risk_status['kill_switch_state'] = value.get(key_upper, 'UNKNOWN')
                
                elif 'EXPOSURE' in key_upper and 'LEVEL' in key_upper:
                    try:
                        risk_status['exposure_level'] = float(str(value.get(key_upper, '0')).replace('%', ''))
                    except (ValueError, TypeError):
                        pass
                
                elif 'DAILY' in key_upper and 'LOSS' in key_upper and 'CAP' in key_upper:
                    try:
                        risk_status['daily_loss_cap'] = float(str(value.get(key_upper, '0')).replace('%', ''))
                    except (ValueError, TypeError):
                        pass
                
                elif 'PORTFOLIO' in key_upper and 'MDD' in key_upper:
                    try:
                        risk_status['portfolio_mdd'] = float(str(value.get(key_upper, '0')).replace('%', ''))
                    except (ValueError, TypeError):
                        pass
                
                elif 'FINAL' in key_upper and 'RISK' in key_upper and 'LEVEL' in key_upper:
                    risk_status['final_risk_level'] = value.get(key_upper, 'UNKNOWN')
            
            # 전체 상태 결정
            if risk_status['kill_switch_state'] == 'ACTIVE':
                risk_status['overall_status'] = 'CRITICAL'
            elif risk_status['final_risk_level'] in ['HIGH', 'CRITICAL']:
                risk_status['overall_status'] = 'HIGH'
            elif risk_status['alerts_count'] > 0:
                risk_status['overall_status'] = 'WARNING'
            else:
                risk_status['overall_status'] = 'NORMAL'
            
            return risk_status
            
        except Exception as e:
            self.logger.error(f"Failed to get risk status: {str(e)}")
            raise
    
    async def update_risk_metrics(
        self,
        kill_switch_state: str = None,
        exposure_level: float = None,
        daily_loss_cap: float = None,
        portfolio_mdd: float = None,
        final_risk_level: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        리스크 지표 업데이트 (편의 메서드)
        
        Args:
            kill_switch_state: 킬 스위치 상태
            exposure_level: 노출 레벨
            daily_loss_cap: 일일 손실 한도
            portfolio_mdd: 포트폴리오 MDD
            final_risk_level: 최종 리스크 레벨
            **kwargs: 추가 지표
            
        Returns:
            Dict[str, Any]: 업데이트 결과
        """
        updates = {}
        
        if kill_switch_state is not None:
            updates['KillSwitch_State'] = kill_switch_state
        if exposure_level is not None:
            updates['Exposure_Level'] = f"{exposure_level:.2f}%"
        if daily_loss_cap is not None:
            updates['Daily_Loss_Cap'] = f"{daily_loss_cap:.2f}%"
        if portfolio_mdd is not None:
            updates['Portfolio_MDD'] = f"{portfolio_mdd:.2f}%"
        if final_risk_level is not None:
            updates['Final_Risk_Level'] = final_risk_level
        
        updates.update(kwargs)
        
        # 각 메트릭 업데이트
        results = {}
        for metric_name, metric_value in updates.items():
            try:
                result = await self.update_dashboard_widget(metric_name, {metric_name: metric_value})
                results[metric_name] = result
            except Exception as e:
                self.logger.warning(f"Failed to update metric '{metric_name}': {str(e)}")
                results[metric_name] = {'error': str(e)}
        
        self.logger.info(f"Updated risk metrics: {list(updates.keys())}")
        return results
