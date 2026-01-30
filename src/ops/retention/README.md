# Retention — 보관 정책 적용 범위 (Phase 9)

## 적용 범위

- **raw**: `raw_snapshot_days` (기본 7일). 경로/파일명에 `raw` 포함 시 적용.
- **pattern**: `pattern_record_days` (기본 30일). 경로/파일명에 `pattern` 포함 시 적용.
- **decision**: `decision_snapshot_days` (기본 None = 무기한 보관). 경로/파일명에 `decision` 포함 시 적용.
- **기타**: 위 키워드가 없으면 보관 기간 미적용(삭제 대상 아님).

## 실패/예외 처리 규칙

- **RetentionCleaner.apply()**: 개별 파일 unlink 실패 시 `logging.warning` 후 다음 파일 계속. 반환값은 성공적으로 삭제된 경로만 포함.
- **호출부**: backup 실패 시 retention 삭제는 수행하지 않음(backup-first). `run_maintenance_automation`은 backup 예외 시 로깅 후 구조화된 summary 반환.
