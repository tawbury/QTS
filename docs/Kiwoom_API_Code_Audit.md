# 키움 REST API ↔ 코드 검수 (openapi.kiwoom.com 기준)

**검수 일자**: 2026-02-01  
**기준**: [키움 REST API](https://openapi.kiwoom.com/main/home) · [API 가이드](https://openapi.kiwoom.com/guide/apiguide)

---

## 1. 웹페이지 기준 스펙 요약

### 1.1 서비스 (웹 메뉴)

| 서비스 | 설명 |
|--------|------|
| 차트정보 | 매매용 차트 |
| 투자자별매매 | 투자자별 매매 상위·차트 |
| 계좌현황 | 계좌평가, 잔고내역 |
| 조건검색 | 키움 조건검색 |
| 시세정보 | 시세 |
| **주문** | **주식 거래·신용** |
| 순위정보 | 거래대금, 신용비율 등 |

### 1.2 OAuth 인증 (접근토큰 발급, au10001)

| 항목 | 스펙 |
|------|------|
| Method | POST |
| URL | `/oauth2/token` |
| 운영 도메인 | `https://api.kiwoom.com` |
| 모의투자 도메인 | `https://mockapi.kiwoom.com` (KRX만 지원) |
| Content-Type | `application/json;charset=UTF-8` |
| **Body** | `grant_type`, **`appkey`**, **`secretkey`** |
| **응답** | **`token`**, `token_type`, **`expires_dt`**, `return_code`, `return_msg` |

### 1.3 국내주식 주문 (주문)

| 항목 | 스펙 |
|------|------|
| Method | **POST** |
| URL | **`/api/dostk/ordr`** |
| Header | `authorization: Bearer {token}`, **`api-id`: TR명 (필수, 최대 10자)** |
| TR명 (api-id) | kt10000(매수), kt10001(매도), **kt10002(주문조회)**, **kt10003(주문취소)** |
| Body (매수/매도) | `dmst_stex_tp`, **`stk_cd`**, **`ord_qty`**, **`ord_uv`**, **`trde_tp`** 등 |

- `dmst_stex_tp`: 국내거래소구분 (KRX, NXT, SOR)
- `stk_cd`: 종목코드
- `ord_uv`: 주문단가
- `trde_tp`: 매매구분 (0:보통, 3:시장가, 5:조건부지정가 등)

### 1.4 알림 (웹 NOTICE)

- **PC 환경**에서 이용 권장
- **장기 미사용 ID**(3년) 접속 제한 → 본인확인 후 해제
- **거래종료 ID** 로그인 제한 → 고객정보 입력 후 이용

---

## 2. 코드 vs 스펙 비교

### 2.1 OAuth (KiwoomClient._get_access_token)

| 항목 | 웹 스펙 | 현재 코드 | 조치 |
|------|---------|-----------|------|
| Body 키 | `secretkey` | `appsecret` | ✅ **수정**: JSON Body에 `secretkey` 사용 (인자명은 `app_secret` 유지 가능) |
| 응답 토큰 필드 | `token` | `access_token` | ✅ **수정**: `data["token"]` 사용 |
| 만료 필드 | `expires_dt` (문자열, 예: 20241107083713) | `expires_in` (초) | ✅ **수정**: `expires_dt` 파싱 후 캐시 만료 계산 |
| 도메인 | api.kiwoom.com / mockapi.kiwoom.com | base_url 인자 | ✅ **문서화**: 기본값으로 운영/모의 도메인 안내 |

### 2.2 주문 API 경로·헤더

| 항목 | 웹 스펙 | 현재 코드 | 조치 |
|------|---------|-----------|------|
| 주문 URL | `POST /api/dostk/ordr` | `POST /api/v1/order` | ✅ **수정**: `/api/dostk/ordr` 사용 |
| Header api-id | 필수 (kt10000/kt10001 등) | 없음 | ✅ **수정**: payload 또는 인자로 api-id 전달 후 헤더 설정 |
| 주문조회 | `POST /api/dostk/ordr`, api-id: kt10002 | `GET /api/v1/order/{id}` | ✅ **수정**: POST /api/dostk/ordr + api-id kt10002 |
| 주문취소 | `POST /api/dostk/ordr`, api-id: kt10003 | `DELETE /api/v1/order/{id}` | ✅ **수정**: POST /api/dostk/ordr + api-id kt10003 |

### 2.3 주문 Body 필드명 (payload_mapping)

| 항목 | 웹 스펙 | 현재 코드 | 조치 |
|------|---------|-----------|------|
| 종목코드 | `stk_cd` | `stock_cd` | ✅ **수정**: `stk_cd` |
| 주문단가 | `ord_uv` | `ord_prc` | ✅ **수정**: `ord_uv` (시장가 시 0 또는 스펙 확인) |
| 매매구분 | `trde_tp` (0/3/5/81 등) | `sell_buy_gubun` + `ord_gubun` | ✅ **수정**: `trde_tp` 단일 필드로 통합 (매수/매도는 api-id로 구분) |
| 거래소구분 | `dmst_stex_tp` (KRX/NXT/SOR) | `market_gubun` ("0" 등) | ✅ **수정**: `dmst_stex_tp` (값 KRX/NXT/SOR) |

### 2.4 기타

| 항목 | 비고 |
|------|------|
| 서명(signature) | 웹 가이드에 요청 서명(HMAC) 필수 여부 불명. 현재 코드는 POST 시 signature 헤더 추가 → 스펙 확정 전까지 유지 또는 선택 처리 |
| 계좌/잔고/포지션 | 웹 메뉴에 “계좌현황” 있음. 현재 `/api/v1/balance`, `/api/v1/positions` 사용 → 실제 TR/URL은 가이드 “계좌” 섹션으로 확정 필요 |
| 오류코드 | 웹 “오류코드” 메뉴 참고하여 `KIWOOM_ERROR_TO_SAFETY` 보강 권장 |

---

## 3. 반영한 코드 수정 요약

1. **KiwoomClient** (`src/runtime/broker/kiwoom/kiwoom_client.py`)
   - OAuth: Body `secretkey`, 응답 `token` / `expires_dt` 반영, 만료 캐시 계산 수정
   - 주문: `POST /api/dostk/ordr`, 헤더 `api-id` (kt10000/kt10001) 반영
   - get_order: POST `/api/dostk/ordr` + api-id kt10002, body `ord_no` (필요 시 dmst_stex_tp 등 가이드 참고)
   - cancel_order: POST `/api/dostk/ordr` + api-id kt10003, body `ord_no`
2. **payload_mapping** (`src/runtime/broker/kiwoom/payload_mapping.py`)
   - `stk_cd`, `ord_uv`, `trde_tp`, `dmst_stex_tp` 사용
   - 주문 payload에 `_api_id`(kt10000/kt10001) 포함 → Client에서 헤더로 사용 후 제거
   - 응답 주문번호 필드 `ord_no` 우선 사용

---

## 4. 참고 링크

- [키움 REST API 홈](https://openapi.kiwoom.com/main/home)
- [API 가이드 (접근토큰 발급 등)](https://openapi.kiwoom.com/guide/apiguide)
