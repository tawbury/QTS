# 명칭 통일: Scalp vs Scalf

Config/Repository/문서에서 **표준 용어**와 **이행 결과**를 정리한다.

**근거:** `docs/arch/13_Config_3분할_Architecture.md`, `docs/arch/00_Architecture.md`

---

## 1. 표준 용어

- **표준:** **Scalp** (영문 표기), 시트명 **Config_Scalp**
- **과거 오표기:** Scalf (오타) — 코드/문서에서 제거·정리 완료

---

## 2. 변경 영향 범위 및 적용 결과

| 구분 | 변경 전 | 변경 후 |
|------|--------|--------|
| 리포지토리 파일 | `config_scalf_repository.py` | `config_scalp_repository.py` |
| 리포지토리 클래스 | `ConfigScalfRepository` | `ConfigScalpRepository` |
| 시트명 | `Config_Scalf` | `Config_Scalp` |
| config_models / sheet_config | (이미 Config_Scalp, SCALP 사용) | 유지 |
| config_local.json 설명 | "Scalf 최소 …" | "Scalp 최소 …" |

- **Imports:** 기존에 `ConfigScalfRepository` / `config_scalf_repository`를 참조하던 코드 없음 → 추가 수정 없음.
- **테스트:** `tests/google_sheets_integration` 내에서 config_scalf 리포지토리 직접 참조 없음.
- **문서:** Repository_Integration_Test_Scope 등에서 Config_Scalf → Config_Scalp, ConfigScalfRepository → ConfigScalpRepository로 반영.

---

## 3. 호환 레이어 / 이행 계획

- **Google 시트 탭 이름:** 운영 중인 스프레드시트에 **Config_Scalf** 탭이 있으면, 탭 이름을 **Config_Scalp**로 변경하면 된다. (코드는 Config_Scalp 시트를 참조한다.)
- **기존 Config_Scalf 탭을 유지해야 하는 경우:** 시트 탭을 Config_Scalp로 이름만 바꾸거나, 복사본 시트를 Config_Scalp로 만들어 사용하면 된다. 별도 호환 레이어(Config_Scalf 시트명 하드코딩)는 두지 않음.

---

## 4. 완료 조건 충족

- [x] 문서와 코드의 전략 스코프 명칭이 일치한다. → Scalp / Config_Scalp로 통일
- [x] 기존 명칭이 남아있다면 “호환 레이어” 또는 “이행 계획”이 문서화되어 있다. → §3
