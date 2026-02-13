"""
Enhanced Performance Repository

성과 대시보드(Performance) 시트를 관리하는 리포지토리입니다.
Dashboard 타입: 블록 단위로 셀 주소 기반 읽기/쓰기.
스키마: config/schemas/gssheet.json Performance 블록 정의.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .base_dashboard_repository import BaseDashboardRepository


class EnhancedPerformanceRepository(BaseDashboardRepository):
    """
    Enhanced Performance 리포지토리 (Dashboard 타입)

    Performance 시트는 블록(KPI Summary, Cumulative Return, Monthly Trend 등)으로 구성.
    각 블록의 셀 주소는 gssheet.json에 정의됨.
    """

    SHEET_NAME = "Performance"

    # gssheet.json 블록별 필드-셀 매핑
    KPI_SUMMARY_FIELDS = {
        "total_return": "B2",
        "mdd": "C2",
        "daily_vol": "D2",
        "sharpe": "E2",
        "win_rate": "F2",
        "avg_win": "G2",
        "avg_loss": "H2",
    }

    SUMMARY_TABLE_FIELDS = {
        "date": "A46",
        "daily_pnl": "B46",
        "cum_pnl": "C46",
        "return_pct": "D46",
        "mdd": "E46",
        "exposure": "F46",
        "drawdown": "G46",
        "notes": "H46",
    }

    def update_kpi_summary(self, kpi_data: Dict[str, Any]) -> bool:
        """
        KPI Summary 블록 업데이트.

        Args:
            kpi_data: {"total_return": "12.5%", "mdd": "-3.2%", "sharpe": "1.85", ...}
        """
        success = True
        for field_name, value in kpi_data.items():
            cell_address = self.KPI_SUMMARY_FIELDS.get(field_name)
            if cell_address and value is not None:
                if not self._update_cell(cell_address, value):
                    success = False
        self.logger.info(f"Updated KPI Summary: {list(kpi_data.keys())}")
        return success

    def get_kpi_summary(self) -> Dict[str, Any]:
        """KPI Summary 블록 조회"""
        result = {}
        for field_name, cell_address in self.KPI_SUMMARY_FIELDS.items():
            result[field_name] = self._get_cell(cell_address)
        return result

    def update_summary_table(self, rows: List[Dict[str, Any]]) -> bool:
        """
        Summary Table 블록 업데이트 (다중 행).

        Args:
            rows: [{"date": "2026-02-13", "daily_pnl": 5000, ...}, ...]
        """
        try:
            ws = self._get_worksheet()
            data = []
            for row in rows:
                data.append([
                    row.get("date", ""),
                    row.get("daily_pnl", ""),
                    row.get("cum_pnl", ""),
                    row.get("return_pct", ""),
                    row.get("mdd", ""),
                    row.get("exposure", ""),
                    row.get("drawdown", ""),
                    row.get("notes", ""),
                ])
            if data:
                start_row = 46
                end_row = start_row + len(data) - 1
                ws.update(data, range_name=f"A{start_row}:H{end_row}")
                self.logger.info(f"Updated Summary Table: {len(data)} rows")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update Summary Table: {str(e)}")
            return False

    def update_monthly_trend(self, months: List[Dict[str, Any]]) -> bool:
        """
        Monthly Trend 블록 업데이트.

        Args:
            months: [{"month": "2026-01", "monthly_return": "3.2%", ...}, ...]
        """
        try:
            ws = self._get_worksheet()
            data = []
            for m in months:
                data.append([
                    m.get("month", ""),
                    m.get("monthly_return", ""),
                    m.get("cumulative_monthly_return", ""),
                    m.get("mom_change", ""),
                ])
            if data:
                start_row = 21
                end_row = start_row + len(data) - 1
                ws.update(data, range_name=f"A{start_row}:D{end_row}")
                self.logger.info(f"Updated Monthly Trend: {len(data)} rows")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update Monthly Trend: {str(e)}")
            return False
