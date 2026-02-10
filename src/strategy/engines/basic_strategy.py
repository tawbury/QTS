from typing import Dict, Any, Optional
import logging

class BasicStrategy:
    """
    기본 전략: 단순히 항상 HOLD 또는 테스트용 신호를 반환
    """
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger("BasicStrategy")

    def calculate_signal(self, market_data: Dict[str, Any], position_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        symbol = market_data.get('symbol')
        price_val = market_data.get('price', 0.0)
        close_price = float(price_val.get('close', 0.0)) if isinstance(price_val, dict) else float(price_val or 0.0)
        prev_close = float(market_data.get('prev_close', 0.0))
        pos = position_data if isinstance(position_data, dict) else {}
        current_qty = pos.get('quantity', 0) if pos else 0
        # 가격이 전일종가와 다르면 BUY, 아니면 HOLD
        if close_price != prev_close:
            return {
                'symbol': symbol,
                'action': 'BUY',
                'qty': 1,
                'weight': 1.0,
                'price': close_price,
                'timestamp': market_data.get('timestamp'),
                'reason': f'BasicStrategy: BUY (close={close_price}, prev_close={prev_close})'
            }
        else:
            return {
                'symbol': symbol,
                'action': 'HOLD',
                'qty': 0,
                'weight': 0.0,
                'price': close_price,
                'timestamp': market_data.get('timestamp'),
                'reason': 'BasicStrategy: HOLD (no price change)'
            }
