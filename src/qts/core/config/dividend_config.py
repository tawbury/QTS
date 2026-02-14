"""
Dividend Configuration Management

로컬 배당 정보 데이터베이스를 관리합니다.
로컬 JSON 파일 기반 Dividend 설정 기능입니다.
로깅/오류 처리 규칙: local_config.py와 동일한 패턴(ConfigLoadResult, 로깅).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .config_constants import (
    DIVIDEND_DB_FILENAME,
    LOCAL_CONFIG_DIR,
    LOCAL_CONFIG_SUBDIR,
)
from .config_models import ConfigEntry, ConfigLoadResult, ConfigScope

_LOG = logging.getLogger(__name__)


def _dividend_json_error(exc: json.JSONDecodeError) -> str:
    """JSONDecodeError를 사용자 친화적 메시지로 변환 (dividend DB용)."""
    msg = f"JSON 형식 오류 (줄 {exc.lineno}, 열 {exc.colno})"
    if getattr(exc, "msg", None):
        msg += f": {exc.msg}"
    return msg


class DividendConfig:
    """
    배당 정보 설정 관리자
    
    로컬 파일 기반의 배당 정보 데이터베이스를 관리합니다.
    """
    
    def __init__(self, project_root: Path):
        """
        DividendConfig 초기화
        
        Args:
            project_root: 프로젝트 루트 경로
        """
        self.project_root = project_root
        self.config_path = (
            project_root / LOCAL_CONFIG_DIR / LOCAL_CONFIG_SUBDIR / DIVIDEND_DB_FILENAME
        )
        self._ensure_config_dir()
    
    def _ensure_config_dir(self) -> None:
        """설정 디렉토리 생성"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load_dividend_db(self) -> ConfigLoadResult:
        """
        배당 정보 데이터베이스 로드
        
        Returns:
            ConfigLoadResult: 로드 결과
        """
        try:
            if not self.config_path.exists():
                return ConfigLoadResult(
                    ok=True,
                    scope=ConfigScope.LOCAL,
                    entries=[],
                    error=None,
                    source_path=str(self.config_path)
                )
            
            with open(self.config_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            
            # JSON 데이터를 ConfigEntry 리스트로 변환
            entries = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        entry = ConfigEntry(
                            category=item.get('category', 'DIVIDEND_DB'),
                            subcategory=item.get('subcategory', 'DIVIDEND_INFO'),
                            key=item.get('key', ''),
                            value=str(item.get('value', {})),
                            description=item.get('description', ''),
                            tag=item.get('tag', 'DIVIDEND')
                        )
                        entries.append(entry)
            elif isinstance(data, dict):
                # 단일 엔트리 처리
                entry = ConfigEntry(
                    category=data.get('category', 'DIVIDEND_DB'),
                    subcategory=data.get('subcategory', 'DIVIDEND_INFO'),
                    key=data.get('key', ''),
                    value=str(data.get('value', {})),
                    description=data.get('description', ''),
                    tag=data.get('tag', 'DIVIDEND')
                )
                entries.append(entry)
            
            return ConfigLoadResult(
                ok=True,
                scope=ConfigScope.LOCAL,
                entries=entries,
                error=None,
                source_path=str(self.config_path)
            )
            
        except OSError as e:
            err = (
                f"배당 DB 파일을 읽을 수 없습니다 (인코딩/경로 확인): {e}. "
                f"경로: {self.config_path}"
            )
            _LOG.warning("%s", err)
            return ConfigLoadResult(
                ok=False,
                scope=ConfigScope.LOCAL,
                entries=[],
                error=err,
                source_path=str(self.config_path),
            )
        except json.JSONDecodeError as e:
            err = f"배당 DB {_dividend_json_error(e)}. 파일 형식을 확인하세요."
            _LOG.warning("%s", err)
            return ConfigLoadResult(
                ok=False,
                scope=ConfigScope.LOCAL,
                entries=[],
                error=err,
                source_path=str(self.config_path),
            )
        except Exception as e:
            err = f"배당 DB 로드 중 오류: {e}"
            _LOG.warning("%s", err)
            return ConfigLoadResult(
                ok=False,
                scope=ConfigScope.LOCAL,
                entries=[],
                error=err,
                source_path=str(self.config_path),
            )
    
    def save_dividend_db(self, entries: List[ConfigEntry]) -> bool:
        """
        배당 정보 데이터베이스 저장
        
        Args:
            entries: 저장할 배당 정보 엔트리 리스트
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # ConfigEntry 리스트를 JSON 데이터로 변환
            data = []
            for entry in entries:
                item = {
                    'category': entry.category,
                    'subcategory': entry.subcategory,
                    'key': entry.key,
                    'value': entry.value,
                    'description': entry.description,
                    'tag': entry.tag
                }
                data.append(item)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            _LOG.error("Failed to save dividend DB: %s", e, exc_info=True)
            return False
    
    def get_dividend_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        티커로 배당 정보 조회
        
        Args:
            ticker: 티커
            
        Returns:
            Optional[Dict[str, Any]]: 배당 정보 또는 None
        """
        result = self.load_dividend_db()
        
        if not result.ok:
            return None
        
        for entry in result.entries:
            if entry.key == f"TICKER_{ticker}":
                try:
                    return json.loads(entry.value)
                except json.JSONDecodeError:
                    return entry.value
        
        return None
    
    def get_all_dividend_info(self) -> List[Dict[str, Any]]:
        """
        모든 배당 정보 조회
        
        Returns:
            List[Dict[str, Any]]: 배당 정보 리스트
        """
        result = self.load_dividend_db()
        
        if not result.ok:
            return []
        
        dividend_info = []
        for entry in result.entries:
            if entry.category == 'DIVIDEND_DB':
                try:
                    value = json.loads(entry.value)
                    dividend_info.append(value)
                except json.JSONDecodeError:
                    dividend_info.append(entry.value)
        
        return dividend_info
    
    def add_dividend_info(
        self,
        ticker: str,
        name: str,
        pay_date: str,
        base_date: str,
        dividend_per_share: float,
        qty: int = 0,
        total_dividend: float = 0,
        pay_month: str = "",
        **kwargs
    ) -> bool:
        """
        배당 정보 추가
        
        Args:
            ticker: 티커
            name: 종목명
            pay_date: 지급일
            base_date: 기준일
            dividend_per_share: 주당 배당금
            qty: 보유 수량
            total_dividend: 총 배당금
            pay_month: 지급월
            **kwargs: 추가 정보
            
        Returns:
            bool: 추가 성공 여부
        """
        try:
            result = self.load_dividend_db()
            
            if not result.ok:
                return False
            
            # 기존 엔트리 확인
            entries = result.entries
            for i, entry in enumerate(entries):
                if entry.key == f"TICKER_{ticker}":
                    # 기존 엔트리 업데이트
                    entries[i] = ConfigEntry(
                        category='DIVIDEND_DB',
                        subcategory='DIVIDEND_INFO',
                        key=f"TICKER_{ticker}",
                        value={
                            'ticker': ticker,
                            'name': name,
                            'pay_date': pay_date,
                            'base_date': base_date,
                            'dividend_per_share': dividend_per_share,
                            'qty': qty,
                            'total_dividend': total_dividend,
                            'pay_month': pay_month,
                            **kwargs
                        },
                        description=f"{name} 배당 정보",
                        tag='DIVIDEND'
                    )
                    return self.save_dividend_db(entries)
            
            # 새 엔트리 추가
            new_entry = ConfigEntry(
                category='DIVIDEND_DB',
                subcategory='DIVIDEND_INFO',
                key=f"TICKER_{ticker}",
                value={
                    'ticker': ticker,
                    'name': name,
                    'pay_date': pay_date,
                    'base_date': base_date,
                    'dividend_per_share': dividend_per_share,
                    'qty': qty,
                    'total_dividend': total_dividend,
                    'pay_month': pay_month,
                    **kwargs
                },
                description=f"{name} 배당 정보",
                tag='DIVIDEND'
            )
            
            entries.append(new_entry)
            return self.save_dividend_db(entries)
            
        except Exception as e:
            _LOG.error("Failed to add dividend info: %s", e, exc_info=True)
            return False
    
    def update_dividend_info(self, ticker: str, **kwargs) -> bool:
        """
        배당 정보 업데이트
        
        Args:
            ticker: 티커
            **kwargs: 업데이트할 필드
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            result = self.load_dividend_db()
            
            if not result.ok:
                return False
            
            entries = result.entries
            for i, entry in enumerate(entries):
                if entry.key == f"TICKER_{ticker}":
                    # 기존 정보 업데이트
                    updated_value = entry.value.copy()
                    updated_value.update(kwargs)
                    
                    entries[i] = ConfigEntry(
                        category=entry.category,
                        subcategory=entry.subcategory,
                        key=entry.key,
                        value=updated_value,
                        description=entry.description,
                        tag=entry.tag
                    )
                    return self.save_dividend_db(entries)
            
            return False  # 티커를 찾지 못함
            
        except Exception as e:
            _LOG.error("Failed to update dividend info: %s", e, exc_info=True)
            return False
    
    def delete_dividend_info(self, ticker: str) -> bool:
        """
        배당 정보 삭제
        
        Args:
            ticker: 티커
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            result = self.load_dividend_db()
            
            if not result.ok:
                return False
            
            entries = result.entries
            filtered_entries = [entry for entry in entries if entry.key != f"TICKER_{ticker}"]
            
            if len(entries) == len(filtered_entries):
                return False  # 티커를 찾지 못함
            
            return self.save_dividend_db(filtered_entries)
            
        except Exception as e:
            _LOG.error("Failed to delete dividend info: %s", e, exc_info=True)
            return False
    
    def get_upcoming_dividends(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        다가오는 배당금 조회
        
        Args:
            days: 조회할 일수
            
        Returns:
            List[Dict[str, Any]]: 다가오는 배당금 리스트
        """
        try:
            all_dividends = self.get_all_dividend_info()
            upcoming_dividends = []
            
            end_date = datetime.now().date() + datetime.timedelta(days=days)
            start_date = datetime.now().date()
            
            for dividend in all_dividends:
                pay_date_str = dividend.get('pay_date', '')
                if pay_date_str:
                    try:
                        pay_date = datetime.strptime(pay_date_str, '%Y-%m-%d').date()
                        if start_date <= pay_date <= end_date:
                            upcoming_dividends.append(dividend)
                    except ValueError:
                        continue
            
            # 지급일 순으로 정렬
            upcoming_dividends.sort(key=lambda x: x.get('pay_date', ''))
            
            return upcoming_dividends
            
        except Exception as e:
            _LOG.error("Failed to get upcoming dividends: %s", e, exc_info=True)
            return []
    
    def get_dividend_summary(self) -> Dict[str, Any]:
        """
        배당 정보 요약 조회
        
        Returns:
            Dict[str, Any]: 배당 정보 요약
        """
        try:
            all_dividends = self.get_all_dividend_info()
            
            total_companies = len(all_dividends)
            total_dividend_amount = 0
            companies_with_dividend = 0
            
            for dividend in all_dividends:
                try:
                    dividend_per_share = dividend.get('dividend_per_share', 0)
                    if dividend_per_share:
                        total_dividend_amount += dividend_per_share
                        companies_with_dividend += 1
                except (ValueError, TypeError):
                    continue
            
            summary = {
                'total_companies': total_companies,
                'companies_with_dividend': companies_with_dividend,
                'companies_without_dividend': total_companies - companies_with_dividend,
                'total_dividend_amount': total_dividend_amount,
                'average_dividend_per_company': total_dividend_amount / companies_with_dividend if companies_with_dividend > 0 else 0,
                'dividend_payout_ratio': (companies_with_dividend / total_companies * 100) if total_companies > 0 else 0,
                'last_updated': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            _LOG.error("Failed to get dividend summary: %s", e, exc_info=True)
            return {}
    
    def search_dividend_info(self, query: str) -> List[Dict[str, Any]]:
        """
        배당 정보 검색
        
        Args:
            query: 검색어 (티커 또는 종목명)
            
        Returns:
            List[Dict[str, Any]]: 검색 결과
        """
        try:
            all_dividends = self.get_all_dividend_info()
            search_results = []
            
            query_upper = query.upper()
            
            for dividend in all_dividends:
                ticker = dividend.get('ticker', '').upper()
                name = dividend.get('name', '').upper()
                
                if query_upper in ticker or query_upper in name:
                    search_results.append(dividend)
            
            return search_results
            
        except Exception as e:
            _LOG.error("Failed to search dividend info: %s", e, exc_info=True)
            return []


def load_dividend_config(project_root: Path) -> DividendConfig:
    """
    배당 설정 로드
    
    Args:
        project_root: 프로젝트 루트 경로
        
    Returns:
        DividendConfig: 배당 설정 관리자
    """
    return DividendConfig(project_root)
