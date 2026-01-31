# R_Dash 업데이트 규칙

**관련:** task_02_renderers_and_r_dash_writer.md, docs/arch/06_UI_Architecture.md §4.3, §8.1

## 언제

- **ETEDA 사이클 종료 시** 한 번만 실행한다.
- UI Contract 생성(UIContractBuilder) 직후, Render Engine(R_DashWriter)을 호출한다.

## 어떤 데이터로

- **UI Contract만** 사용한다. Raw/Calc/시트를 직접 읽지 않는다.
- Contract 버전이 기대값과 다르면 R_Dash 갱신을 **중단**한다 (06 §10.1, §10.4).

## ETEDA와의 격리(비동기)

- UI 갱신이 **ETEDA 실행을 블록하지 않도록** 한다.
- 호출 측: `R_DashWriter.schedule_write(contract)` 또는 `asyncio.create_task(writer.write(contract))` 로 **비동기 실행** 권장.
- `write()` 자체는 async이므로, await하지 않고 Task만 반환하면 ETEDA 흐름과 분리된다.
- UI 렌더링 실패는 **매매 중단 사유가 아님** (04_Data_Contract_Spec §7.4).

## 갱신 경로

1. Pipeline 종료 → UI Contract 생성 (UIContractBuilder)
2. R_DashWriter.write(contract) 호출 (또는 schedule_write로 격리)
3. 각 Rendering Unit이 Contract 블록별로 행 데이터 생성
4. Google Sheets API로 해당 영역만 덮어쓰기 (Zero-Formula 유지)
