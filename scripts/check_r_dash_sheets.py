#!/usr/bin/env python3
"""
실시간 상태 감시 UI(R_Dash) Google Sheets 연동 확인.

.env의 GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_KEY 사용.
실행: 프로젝트 루트에서 python scripts/check_r_dash_sheets.py
      또는 PYTHONPATH=src python scripts/check_r_dash_sheets.py
"""

import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트 및 .env
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


async def main():
    creds = os.getenv("GOOGLE_CREDENTIALS_FILE")
    key = os.getenv("GOOGLE_SHEET_KEY")
    if not creds or not key:
        print("SKIP: GOOGLE_CREDENTIALS_FILE or GOOGLE_SHEET_KEY not set in .env")
        return 1
    if not Path(creds).expanduser().exists():
        print(f"SKIP: Credentials file not found: {creds}")
        return 1

    from runtime.data.google_sheets_client import GoogleSheetsClient

    client = GoogleSheetsClient()
    await client.authenticate()
    info = await client.get_spreadsheet_info()

    print("Spreadsheet:", info["title"])
    print("ID:", info["spreadsheet_id"])
    print("Worksheets:", [ws["title"] for ws in info["worksheets"]])

    has_r_dash = any(ws["title"] == "R_Dash" for ws in info["worksheets"])
    print("R_Dash sheet exists:", has_r_dash)

    if has_r_dash:
        try:
            # R_Dash Writer가 쓰는 영역 일부만 샘플 조회 (파이프라인 상태 등)
            sample = await client.get_sheet_data("R_Dash!A1:F10")
            print("R_Dash A1:F10 sample rows:", len(sample))
            if sample:
                print("First row:", sample[0][:5] if len(sample[0]) >= 5 else sample[0])
        except Exception as e:
            print("R_Dash range read note:", e)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
