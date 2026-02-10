#!/usr/bin/env python3
"""
Mock Observer Data Generator

E2E 테스트용 Observer JSONL 데이터를 생성합니다.
Observer 컨테이너에서 실행되어 QTS가 읽을 수 있는 테스트 데이터를 생성합니다.

Usage:
    python generate_mock_files.py

Environment:
    OBSERVER_DATA_DIR: 데이터 저장 경로 (default: /opt/platform/runtime/observer/data)
    MOCK_SYMBOL_COUNT: 생성할 종목 수 (default: 5)
    MOCK_RECORD_COUNT: 종목당 레코드 수 (default: 100)
"""

import json
import os
import random
import sys
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# KST Timezone definition
KST = timezone(timedelta(hours=9))


# 테스트용 종목 데이터
TEST_SYMBOLS = [
    {"symbol": "005930", "name": "삼성전자", "base_price": 71000},
    {"symbol": "000660", "name": "SK하이닉스", "base_price": 185000},
    {"symbol": "035720", "name": "카카오", "base_price": 52500},
    {"symbol": "051910", "name": "LG화학", "base_price": 380000},
    {"symbol": "006400", "name": "삼성SDI", "base_price": 420000},
    {"symbol": "035420", "name": "NAVER", "base_price": 205000},
    {"symbol": "068270", "name": "셀트리온", "base_price": 178000},
    {"symbol": "105560", "name": "KB금융", "base_price": 72000},
    {"symbol": "055550", "name": "신한지주", "base_price": 45000},
    {"symbol": "012330", "name": "현대모비스", "base_price": 235000},
]


def generate_price_tick(base_price: float, volatility: float = 0.02) -> dict:
    """가격 틱 데이터 생성"""
    change_pct = random.uniform(-volatility, volatility)
    current = int(base_price * (1 + change_pct))

    # 시가, 고가, 저가 생성
    open_price = int(base_price * (1 + random.uniform(-volatility/2, volatility/2)))
    high_price = max(current, open_price) + random.randint(0, int(base_price * 0.01))
    low_price = min(current, open_price) - random.randint(0, int(base_price * 0.01))

    return {
        "current": current,
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "change_rate": round(change_pct * 100, 2),
    }


def generate_volume_data(base_price: float) -> dict:
    """거래량 데이터 생성"""
    accumulated = random.randint(50000, 500000)
    trade_value = accumulated * base_price

    return {
        "accumulated": accumulated,
        "trade_value": int(trade_value),
    }


def generate_record(symbol_info: dict, timestamp: datetime, session_id: str) -> dict:
    """단일 레코드 생성"""
    return {
        "timestamp": timestamp.isoformat(),
        "symbol": symbol_info["symbol"],
        "execution_time": timestamp.strftime("%H%M%S"),
        "price": generate_price_tick(symbol_info["base_price"]),
        "volume": generate_volume_data(symbol_info["base_price"]),
        "source": "mock_generator",
        "session_id": session_id,
    }


def generate_jsonl_file(
    output_dir: Path,
    scope: str,
    symbols: list,
    record_count: int,
    date_str: str,
) -> Path:
    """JSONL 파일 생성"""
    scope_dir = output_dir / "assets" / scope
    scope_dir.mkdir(parents=True, exist_ok=True)

    output_file = scope_dir / f"{date_str}.jsonl"
    session_id = f"mock_test_{datetime.now(KST).strftime('%Y%m%d_%H%M%S')}"

    # 시작 시간 (오늘 09:00 KST)
    base_time = datetime.now(KST).replace(hour=9, minute=0, second=0, microsecond=0)

    records = []
    for i in range(record_count):
        # 1초 간격으로 타임스탬프 증가
        current_time = base_time + timedelta(seconds=i)

        for sym in symbols:
            record = generate_record(sym, current_time, session_id)
            records.append(record)

    # 파일에 기록
    with open(output_file, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return output_file


def main():
    """메인 진입점"""
    print("=" * 60)
    print("Mock Observer Data Generator")
    print("=" * 60)

    # 환경변수에서 설정 읽기
    data_dir = Path(os.environ.get(
        "OBSERVER_DATA_DIR",
        "/opt/platform/runtime/observer/data"
    ))
    symbol_count = int(os.environ.get("MOCK_SYMBOL_COUNT", "5"))
    record_count = int(os.environ.get("MOCK_RECORD_COUNT", "100"))

    print(f"Data Directory: {data_dir}")
    print(f"Symbol Count: {symbol_count}")
    print(f"Record Count per Symbol: {record_count}")
    print()

    # 디렉토리 생성
    data_dir.mkdir(parents=True, exist_ok=True)

    # 사용할 종목 선택
    selected_symbols = TEST_SYMBOLS[:symbol_count]
    print(f"Selected Symbols: {[s['symbol'] for s in selected_symbols]}")

    # 오늘 날짜
    today = datetime.now(KST).strftime("%Y%m%d")

    # scalp 및 swing 데이터 생성
    for scope in ["scalp", "swing"]:
        output_file = generate_jsonl_file(
            output_dir=data_dir,
            scope=scope,
            symbols=selected_symbols,
            record_count=record_count,
            date_str=today,
        )
        total_records = symbol_count * record_count
        print(f"Generated: {output_file} ({total_records} records)")

    print()
    print("=" * 60)
    print("Mock data generation completed successfully!")
    print("=" * 60)

    # 생성된 파일 목록 출력
    print("\nGenerated files:")
    for scope in ["scalp", "swing"]:
        scope_dir = data_dir / "assets" / scope
        if scope_dir.exists():
            for f in scope_dir.glob("*.jsonl"):
                size = f.stat().st_size
                print(f"  - {f}: {size:,} bytes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
