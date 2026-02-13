"""
Enhanced Portfolio Repository

포트폴리오 대시보드(Portfolio) 시트를 관리하는 리포지토리입니다.
Dashboard 타입: 블록 단위로 셀 주소 기반 읽기/쓰기.
스키마: config/schemas/gssheet.json Portfolio 블록 정의.
"""
from __future__ import annotations

from typing import Any, Dict

from .base_dashboard_repository import BaseDashboardRepository


class EnhancedPortfolioRepository(BaseDashboardRepository):
    """
    Enhanced Portfolio 리포지토리 (Dashboard 타입)

    Portfolio 시트는 블록(KPI Overview, Risk Summary, Allocation 등)으로 구성.
    각 블록의 셀 주소는 gssheet.json에 정의됨.
    """

    SHEET_NAME = "Portfolio"

    # gssheet.json 블록별 필드-셀 매핑
    KPI_OVERVIEW_FIELDS = {
        "total_equity": "B2",
        "daily_pnl": "D2",
        "exposure": "G2",
        "cash_ratio": "J2",
        "holdings_count": "M2",
        "killswitch_status": "P2",
    }

    RISK_SUMMARY_FIELDS = {
        "exposure_flag": "T2",
        "volatility_flag": "T4",
        "pnl_flag": "T6",
        "concentration_flag": "T8",
        "market_flag": "T10",
    }

    PORTFOLIO_ALLOCATION_FIELDS = {
        "symbol": "V2",
        "market_value": "W2",
        "weight": "X2",
    }

    def update_kpi_overview(self, kpi_data: Dict[str, Any]) -> bool:
        """
        KPI Overview 블록 업데이트.

        Args:
            kpi_data: {"total_equity": 1000000, "daily_pnl": 5000, ...}
        """
        success = True
        for field_name, value in kpi_data.items():
            cell_address = self.KPI_OVERVIEW_FIELDS.get(field_name)
            if cell_address and value is not None:
                if not self._update_cell(cell_address, value):
                    success = False
        self.logger.info(f"Updated KPI Overview: {list(kpi_data.keys())}")
        return success

    def get_kpi_overview(self) -> Dict[str, Any]:
        """KPI Overview 블록 조회"""
        result = {}
        for field_name, cell_address in self.KPI_OVERVIEW_FIELDS.items():
            result[field_name] = self._get_cell(cell_address)
        return result

    def update_risk_summary(self, risk_data: Dict[str, Any]) -> bool:
        """
        Risk Summary 블록 업데이트.

        Args:
            risk_data: {"exposure_flag": "GREEN", "volatility_flag": "YELLOW", ...}
        """
        success = True
        for field_name, value in risk_data.items():
            cell_address = self.RISK_SUMMARY_FIELDS.get(field_name)
            if cell_address and value is not None:
                if not self._update_cell(cell_address, value):
                    success = False
        self.logger.info(f"Updated Risk Summary: {list(risk_data.keys())}")
        return success

    def update_portfolio_allocation(self, allocations: list[Dict[str, Any]]) -> bool:
        """
        Portfolio Allocation 블록 업데이트 (다중 행).

        Args:
            allocations: [{"symbol": "005930", "market_value": 1000000, "weight": "10%"}, ...]
        """
        try:
            ws = self._get_worksheet()
            rows = []
            for alloc in allocations:
                rows.append([
                    alloc.get("symbol", ""),
                    alloc.get("market_value", ""),
                    alloc.get("weight", ""),
                ])
            if rows:
                start_row = 2
                end_row = start_row + len(rows) - 1
                ws.update(rows, range_name=f"V{start_row}:X{end_row}")
                self.logger.info(f"Updated Portfolio Allocation: {len(rows)} rows")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update Portfolio Allocation: {str(e)}")
            return False
