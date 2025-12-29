
---

# autoclean

## Structure Audit & Cleanup Tool

### Storage & Artifact Management Specification

* **Project Name:** `autoclean`
* **Version:** v1.0.0
* **Status:** Enforcing
* **Scope:** `Root/tools/autoclean`

---

## 1. 프로젝트 정의 (Revised)

`autoclean`은 다음을 목적으로 하는 **범용 코드베이스 정리 도구**다.

* 폴더 + 파일 **구조 스냅샷**
* 실제 사용 중인 파일 분석(AST)
* 삭제 후보 탐지 및 사용자 검증
* 선택적 백업(zip)
* 선택적 정리 실행
* 변경 이력 기록

본 도구는 **특정 프로젝트(QTS 등)에 종속되지 않으며**,
어떤 코드 프로젝트에서도 동일한 구조와 규칙으로 사용 가능하다.

---

## 2. Root 추상화 규칙 (변경 없음)

* 실제 프로젝트 루트 이름은 출력에 사용하지 않는다
* 모든 구조 출력은 **의미적 루트 표기**를 사용한다

```txt
Root/
├─ src/
├─ tests/
└─ tools/
```

> 이 규칙은 autoclean의 **범용성 보장 규칙**이다.

---

## 3. 디렉토리 최상위 구조 (프로젝트명 반영)

```txt
Root/
└─ tools/
   └─ autoclean/
      ├─ history/
      ├─ artifacts/
      ├─ rules.py
      ├─ scan_used_files.py
      ├─ detect_garbage.py
      ├─ cleanup.py
      ├─ apply_cleanup.py
      ├─ backup_before_cleanup.py
      ├─ snapshot.py
      ├─ snapshot_diff.py
      └─ README.md
```

### 변경 요약

* ❌ `Autocleanfolder`
* ❌ `AutoCleanFolder`
* ❌ `*folder` 계열 명칭
  → ✅ **`autoclean` 단일 명칭으로 통일**

---

## 4. history/ 디렉토리 스펙 (최종 결과물 전용)

### 4.1 역할

`history/`는 **사람이 검토·보존할 가치가 있는 결과물만 저장**한다.

* 실행 결과 로그
* 구조 스냅샷
* 변경 diff

### 4.2 저장 대상 (허용)

| 파일                              | 설명          |
| ------------------------------- | ----------- |
| `tree_full_YYYYMMDD_HHMMSS.txt` | 전체 구조 스냅샷   |
| `tree_used_YYYYMMDD_HHMMSS.txt` | 사용 중 구조 스냅샷 |
| `tree_*_latest.txt`             | 기준용 최신 스냅샷  |
| `diff_YYYYMMDD_HHMMSS.txt`      | 구조 변경 diff  |
| `cleanup.log`                   | 실제 삭제 실행 로그 |

### 4.3 금지 사항

* JSON ❌
* ZIP ❌
* 임시 파일 ❌

> **history는 “결과 전용” 디렉토리다.**

---

## 5. artifacts/ 디렉토리 스펙 (중간 산출물 전용)

### 5.1 역할

`artifacts/`는 실행 과정에서 생성되지만
**다음 실행 시 덮어써도 무방한 파일**을 저장한다.

* 판단 보조
* 실행 캐시
* 백업(단기)

### 5.2 하위 구조 (권장)

```txt
artifacts/
├─ used/
│  └─ used_files.json
├─ garbage/
│  └─ garbage_report.json
├─ backup/
│  └─ structure_cleanup_backup.zip
└─ tmp/
```

### 5.3 저장 대상

| 파일                             | 설명                |
| ------------------------------ | ----------------- |
| `used_files.json`              | AST 기반 사용 파일 목록   |
| `garbage_report.json`          | 삭제 후보 탐지 결과       |
| `structure_cleanup_backup.zip` | 삭제 전 백업 (항상 덮어쓰기) |
| `tmp/*`                        | 필요 시 확장           |

### 5.4 수명 정책

* 보존 의무 없음
* 언제든 정리 가능
* 감사 대상 ❌

---

## 6. 파일 생성 책임 분리 (불변 규칙)

| 계층      | 저장 위치           |
| ------- | --------------- |
| 스캔 / 판단 | `artifacts/`    |
| 실행 결과   | `history/`      |
| 정책 정의   | 코드 (`rules.py`) |

이 규칙을 어기면 **구조 의미가 붕괴**된다.

---

## 7. 기존 코드에 대한 적용 가이드

### 7.1 즉시 수정 대상 (경로 상수만)

아래 항목들은 **로직 변경 없이 경로만 수정**한다.

* `USED_JSON`
* `REPORT_JSON`
* `SNAPSHOT_DIR`
* `BACKUP_NAME / BACKUP_DIR`
* `cleanup.log`

### 7.2 수정 방향

* 모든 중간 산출물 → `Root/tools/autoclean/artifacts/`
* 모든 결과 로그/스냅샷 → `Root/tools/autoclean/history/`

---

## 8. README.md에 명시해야 할 핵심 선언

> autoclean은 특정 프로젝트에 종속되지 않는
> 구조 감사 및 정리 자동화 도구이다.
>
> * Root 기준 구조 출력
> * history: 결과 보존
> * artifacts: 실행 보조

---

## 9. 스펙 효력

* 본 문서는 **v1.0.0 기준 강제 스펙**
* 이후 구조 변경은 반드시 버전 업 선행
* 리팩토링은 스펙을 침범하지 않는 선에서만 허용

---

