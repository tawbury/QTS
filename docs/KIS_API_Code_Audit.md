# KIS Open API ↔ 코드 검수 (open-trading-api 기준)

**검수 일자**: 2026-02-01  
**기준**: [koreainvestment/open-trading-api](https://github.com/koreainvestment/open-trading-api) · `examples_llm/domestic_stock/order_cash/order_cash.py` · `kis_auth.py`

---

## 1. 공식 샘플 기준 스펙 요약

### 1.1 주문(현금) API (order_cash)

| 항목 | 스펙 |
|------|------|
| API URL | `/uapi/domestic-stock/v1/trading/order-cash` |
| Method | POST |
| **tr_id (실전)** | TTTC0011U(매도), TTTC0012U(매수) |
| **tr_id (모의)** | VTTC0011U(매도), VTTC0012U(매수) |
| Body 키 | **대문자 필수**: CANO, ACNT_PRDT_CD, PDNO, ORD_DVSN, ORD_QTY, ORD_UNPR, EXCG_ID_DVSN_CD, SLL_TYPE, CNDT_PRIC |
| 매수/매도 | Body에 없음. **tr_id로 구분** (0011=매도, 0012=매수) |
| EXCG_ID_DVSN_CD | 거래소 (예: "KRX") |
| 응답 | rt_cd (0=성공), body.output (주문 결과) |

### 1.2 인증 (kis_auth.py)

| 항목 | 스펙 |
|------|------|
| URL | `{domain}/oauth2/tokenP` |
| Body | grant_type, **appkey**, **appsecret** |
| 응답 | **access_token**, **access_token_token_expired** (만료일시) |

---

## 2. 코드 vs 스펙 비교

### 2.1 tr_id (KISClient)

| 항목 | 공식 샘플 | 현재 코드 | 조치 |
|------|-----------|-----------|------|
| 실전 매도/매수 | TTTC0011U / TTTC0012U | TTTC0801U / TTTC0802U | ✅ **수정**: 0011/0012 사용 |
| 모의 매도/매수 | VTTC0011U / VTTC0012U | VTTC0801U / VTTC0802U | ✅ **수정**: 0011/0012 사용 |

### 2.2 주문 Body (payload_mapping)

| 항목 | 공식 스펙 | 현재 코드 | 조치 |
|------|-----------|-----------|------|
| Body 키 | 대문자 (CANO, PDNO, ORD_DVSN, ORD_QTY, ORD_UNPR, EXCG_ID_DVSN_CD 등) | SLL_BUY_DVSN_CD 포함, 일부 소문자 | ✅ **수정**: SLL_BUY_DVSN_CD 제거(tr_id로 구분), EXCG_ID_DVSN_CD 사용 |
| EXCG_ID_DVSN_CD | "KRX" 등 | market "KR" | ✅ **수정**: KR→KRX 매핑, 키명 EXCG_ID_DVSN_CD |
| SLL_TYPE, CNDT_PRIC | 선택 | 없음 | ✅ **수정**: 빈 문자열 기본값 추가 |

### 2.3 place_order 전송 Body (KISClient)

| 항목 | 비고 |
|------|------|
| 전송 Body | API에 보낼 때 **대문자 키만** 포함. "side", "symbol" 등 메타는 제외. |

### 2.4 응답 파싱 (parse_kis_place_response)

| 항목 | 공식 스펙 | 현재 코드 | 조치 |
|------|-----------|-----------|------|
| 성공 여부 | rt_cd == "0" | ok, order_id | ✅ **수정**: rt_cd 및 body.output 기반 파싱 |
| 주문번호 | output.ODNO 등 | order_id, ord_no | ✅ **수정**: output 내 필드 확인 후 매핑 |

---

## 3. 반영한 코드 수정 요약

1. **KISClient** (`src/runtime/broker/kis/kis_client.py`)
   - tr_id: 0801/0802 → **0011(매도)/0012(매수)** (실전·모의 동일 규칙)
   - place_order: API로 보낼 body에서 **대문자 키만** 포함 (side/symbol 제외)
2. **payload_mapping** (`src/runtime/broker/kis/payload_mapping.py`)
   - Body: CANO, ACNT_PRDT_CD, PDNO, ORD_DVSN, ORD_QTY, ORD_UNPR, **EXCG_ID_DVSN_CD**, SLL_TYPE, CNDT_PRIC
   - SLL_BUY_DVSN_CD 제거 (매수/매도는 tr_id로 구분)
   - market "KR" → EXCG_ID_DVSN_CD "KRX"
   - "side"는 tr_id 선택용으로만 유지(전송 시 제외)
3. **parse_kis_place_response**
   - rt_cd, msg_cd, msg1, output 기반으로 성공/실패 및 주문번호 파싱

---

## 4. 참고 링크

- [KIS Open API GitHub](https://github.com/koreainvestment/open-trading-api)
- [한국투자증권 API 포털](https://apiportal.koreainvestment.com)
