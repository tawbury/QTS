# Phase 8 — Broker Integration: Multi-Broker Adapter Pattern

## 목표

- Multi-Broker 확장 가능한 Adapter Pattern 구현
- Broker Engine Interface 표준화 완성

## 근거

- 현재 KIS(한국투자증권) 어댑터만 있고 확장성 구조 부족
- Broker Adapter 패턴이 제대로 구현되지 않음
- 아키텍처 문서의 Multi-Broker 확장 원칙 구현 필요

## 작업

- [x] Broker Adapter Pattern 설계
  - [x] `src/runtime/broker/adapters/base_adapter.py` (BaseBrokerAdapter: OrderAdapter + broker_id)
  - [x] 표준화된 Broker Interface: OrderAdapter 계약 + broker_id/name()
  - [x] Adapter 등록/선택: `registry.py` (register_broker, get_broker, list_broker_ids), lazy KIS/Kiwoom 등록
- [x] Kiwoom Broker Adapter 구현
  - [x] `src/runtime/broker/adapters/kiwoom_adapter.py` (스켈레톤, Kiwoom API 연동은 추후)
  - [x] KIS와 동일 OrderAdapter 계약 (place_order/get_order/cancel_order, dry_run 수용)
- [x] Multi-Broker 지원 강화
  - [x] Broker 선택: get_broker(broker_id, **kwargs), get_broker_for_config(config)
  - [x] Broker별 Fail-Safe: KIS는 payload_mapping; Kiwoom은 추후 동일 패턴 확장
  - [ ] **Load Balancing 및 Fallback 전략**: BrokerConfig.fallback_broker_id 구조만 확보, 전환 로직은 호출부에서 구현  
    **진행 시기**: Kiwoom 실연동 완료 후, 또는 Primary 브로커 장애 시 자동 전환 요구가 발생할 때. (실제 failover 호출부 구현)
- [x] Broker Configuration Management
  - [x] BrokerConfig(broker_id, fallback_broker_id, kwargs), broker_id_from_config(sheet, env, default)
  - [ ] **Config 시트 연동**: 시트에서 broker_id 읽어 broker_id_from_config에 전달하는 직접 바인딩 미구현  
    **진행 시기**: Config_Scalp/Config_Swing 시트에 BROKER_ID(또는 `system.broker.primary_id` 등) 행 추가 후, ETEDA/실행 루프에서 `config.get_flat("system.broker.primary_id")` 등으로 읽어 `broker_id_from_config(sheet_broker_id=..., env_broker_id=os.getenv("BROKER_ID"))`에 넘기는 연동 단계. (.env에 `GOOGLE_SHEET_KEY`, `GOOGLE_CREDENTIALS_FILE` 있음 → 시트 접속 가능)

## 완료 조건

- [x] Multi-Broker Adapter Pattern이 구현됨
- [x] KIS, Kiwoom Broker가 모두 지원됨 (Kiwoom은 스켈레톤)
- [x] Broker 확장이 용이한 구조가 확보됨 (등록/선택/Config)
