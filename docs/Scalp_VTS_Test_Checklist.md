# 모의투자(VTS) 스캘프 거래 테스트 점검 체크리스트

**검수 일자**: 2026-02-01  
**목적**: 실제 모의투자로 스캘프 위주 거래를 테스트할 때 필요한 설정·전략값·점검 항목

---

## 1. 핵심 이슈 (사전 확인 필수)

### 1.1 시세 데이터 공급원 — ⚠️ 현재 미연동

| 항목 | 현황 | 영향 |
|------|------|------|
| **프로덕션 snapshot_source** | `None` (main.py) | `_default_snapshot()`만 사용 → `observation.inputs.price` 없음 |
| **Extract 단계** | `inputs` 또는 `price` 없으면 `return None` | **run_once → "no_market_data"로 즉시 skip** |
| **실제 거래 루프** | 시세 없으면 파이프라인 미가동 | BUY/SELL 시그널 생성 불가 |

**결론**: 현재 프로덕션 모드(`--broker kis --scope scalp`)로 실행해도 **시세가 공급되지 않아 ETEDA 파이프라인이 매 사이클 "no_market_data"로 skip**됩니다.  
KIS/Kiwoom WebSocket 실시간 시세 연동 또는 별도 시세 공급 소스 구현이 필요합니다.

**임시 대안**: `--local-only` 모드의 `MockSnapshotSource`처럼, 프로덕션용 **간단 시세 공급기**를 주입하여 테스트 가능. (예: KIS REST 현재가 조회 → snapshot 생성)

---

## 2. Config_Local 필수 키 (모의투자용 권장값)

| KEY | 권장값 (모의투자) | 설명 |
|-----|-------------------|------|
| INTERVAL_MS | 5000~10000 | 스캘프는 짧은 주기. 5초~10초 권장 (API 제한 고려) |
| ERROR_BACKOFF_MS | 5000 | 연속 오류 시 대기 시간 |
| ERROR_BACKOFF_MAX_RETRIES | 5 | 연속 오류 허용 횟수 |
| RUN_MODE | PAPER 또는 SIM | 모의투자 = PAPER |
| LIVE_ENABLED | N | 실전 주문 비활성화 |
| trading_enabled | Y | 거래 활성화 (N이면 Act skip) |
| PIPELINE_PAUSED | N | Y이면 루프 즉시 중단 |
| KS_ENABLED | Y | Kill Switch 활성화 권장 |
| BASE_EQUITY | 10000000 | 기준 자산 (원). 리스크 계산용 |
| KILLSWITCH_STATUS | OFF | ON/ACTIVE이면 Act skip |
| safe_mode | N | 1/true이면 Act skip |

---

## 3. Config_Scalp 시트 (Google Sheet)

### 3.1 아키텍처 권장 범위 (13_Config_3분할_Architecture.md §4.2)

| 범주 | 필수 포함 | 예시 KEY |
|------|----------|----------|
| Entry/Signal | 기술적 지표/신호 | scalp_rsi_oversold, scalp_rsi_overbought |
| Exit Rule | 손절/익절/시간 기반 중 1개 이상 | scalp_stop_loss_pct, scalp_take_profit_pct, scalp_max_hold_sec |
| Risk Control | 단건 손실 제한 또는 변동성 제한 | scalp_max_loss_pct, scalp_volatility_limit |
| Position | 최대 포지션 수 또는 단건 비중 | scalp_position_limit, scalp_max_qty_per_order |

### 3.2 ConfigScalpRepository 지원 카테고리

코드에서 `get_*_parameters()`로 조회 가능한 카테고리:

| 카테고리 | 용도 |
|----------|------|
| GOLDEN_CROSS | 골든크로스 파라미터 |
| RSI | RSI 과매도/과매수 등 |
| BOLLINGER_BANDS | 볼린저 밴드 |
| EXECUTION | 실행 관련 설정 |
| TIMEFRAME | 타임프레임 |

### 3.3 Config_Scalp 시트 컬럼

- `CATEGORY | SUB_CATEGORY | KEY | VALUE | DESCRIPTION | TAG`
- 예시 행:

| CATEGORY | SUB_CATEGORY | KEY | VALUE | DESCRIPTION |
|----------|--------------|-----|-------|-------------|
| RSI | SIGNAL | scalp_rsi_oversold | 30 | RSI 과매도 매수 신호 |
| RSI | SIGNAL | scalp_rsi_overbought | 70 | RSI 과매수 매도 신호 |
| RISK | LOSS | scalp_max_loss_pct | 2 | 단일 종목 최대 손실 % |
| RISK | POSITION | scalp_position_limit | 5 | 최대 동시 포지션 수 |
| EXECUTION | ORDER | scalp_max_qty_per_order | 10 | 1회 주문 최대 수량 |

**참고**: 현재 `StrategyEngine.calculate_signal()`은 Config_Scalp를 **직접 사용하지 않음**. 기본 HOLD만 반환. 실제 스캘프 전략 연동 시 위 파라미터를 읽어 사용해야 함.

---

## 4. .env (Broker VTS)

### 4.1 KIS 모의투자

```
KIS_MODE=KIS_VTS
KIS_VTS_APP_KEY=<한국투자증권 앱키>
KIS_VTS_APP_SECRET=<앱시크릿>
KIS_VTS_ACCOUNT_NO=<모의투자 계좌번호>
KIS_VTS_ACNT_PRDT_CD=01
KIS_VTS_BASE_URL=https://openapivts.koreainvestment.com:29443
```

### 4.2 Kiwoom 모의투자

```
KIWOOM_MODE=KIWOOM_VTS
KIWOOM_VTS_APP_KEY=...
KIWOOM_VTS_APP_SECRET=...
KIWOOM_VTS_ACCOUNT_NO=...
KIWOOM_VTS_ACNT_PRDT_CD=01
KIWOOM_VTS_BASE_URL=https://mockapi.kiwoom.com
```

### 4.3 실전 주문 스위치

```
ENABLE_REAL_ORDER=N
```

모의투자에서는 REAL 모드를 쓰지 않으므로 영향 없음. VTS 모드는 항상 모의 체결.

---

## 5. Google Sheets

| 항목 | 필수 | 확인 |
|------|------|------|
| GOOGLE_SHEET_KEY | ✅ | 스프레드시트 ID |
| GOOGLE_CREDENTIALS_FILE | ✅ | 서비스 계정 JSON 경로 |
| Config_Scalp 시트 | ✅ | 시트 탭 이름 정확히 `Config_Scalp` |
| Config_Scalp 컬럼 | ✅ | CATEGORY, SUB_CATEGORY, KEY, VALUE 등 |
| Position 시트 | ⚠️ | 포지션 조회용 (없으면 빈 결과) |
| T_Ledger 시트 | ⚠️ | 거래 기록 (현재 Act 후 자동 기록 안 됨) |

---

## 6. 전략·엔진 현황

### 6.1 StrategyEngine

| 항목 | 현황 |
|------|------|
| **calculate_signal()** | 기본 HOLD만 반환 |
| **Config_Scalp 연동** | 미구현 |
| **SimpleStrategy** | buy_below, sell_above 등 파라미터 있으나 ETEDA 경로에서 미사용 |

### 6.2 BUY/SELL 시그널 발생 조건

현재 코드상 BUY/SELL이 나오려면:

1. `StrategyEngine`을 **다른 전략으로 교체**하거나
2. `calculate_signal()` 로직을 수정하여 Config_Scalp 기반 신호 생성

`test_main_mock_run.py`의 `ForceSignalStrategyEngine`처럼 강제 시그널을 주입하면 Act까지 도달 가능.

---

## 7. KIS VTS 모의투자 특이사항

| 항목 | 내용 |
|------|------|
| **거래 시간** | 실거래와 동일 (09:00~15:30, 동시호가 제외). 시간 외 주문은 별도 |
| **API 제한** | 토큰 1분당 1회 제한. Hashkey는 POST 요청마다 필요 |
| **체결** | 모의 체결. 실제 시세 기반 시뮬레이션 |
| **잔고/포지션** | `get_balance()`로 모의 계좌 조회 가능 |

---

## 8. 테스트 실행 전 체크리스트

- [ ] .env에 KIS_VTS_* 또는 KIWOOM_VTS_* 설정 완료
- [ ] `python test_broker_auth.py` 통과 (인증 확인)
- [ ] Google Sheet에 Config_Scalp 시트 존재 및 KEY/VALUE 행 추가
- [ ] config_local.json에 trading_enabled=Y, PIPELINE_PAUSED=N
- [ ] RUN_MODE=PAPER 또는 SIM
- [ ] **시세 공급** 방안 결정 (WebSocket 미구현 시 REST 주기 조회 또는 Mock 주입)
- [ ] (선택) `python test_kis_order.py`로 1주 시장가 매수 테스트

---

## 9. 실행 명령

```bash
# KIS 모의투자 + 스캘프 Config
python main.py --broker kis --scope scalp -v

# Kiwoom 모의투자
python main.py --broker kiwoom --scope scalp -v
```

---

## 10. 알려진 제한사항 요약

| 제한 | 영향 |
|------|------|
| **시세 미공급** | 프로덕션 모드에서 매 사이클 no_market_data skip |
| **StrategyEngine HOLD 고정** | BUY/SELL 시그널 미발생 |
| **T_Ledger 미기록** | 주문 성공/실패가 시트에 저장되지 않음 |
| **Safety Hook None** | record_fail_safe 호출 대상 없음 |

이 제한들을 해소하면 모의투자 스캘프 테스트가 end-to-end로 동작합니다.
