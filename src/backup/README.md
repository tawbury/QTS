# Backup — 산출물 및 복구 절차 (Phase 9)

## 백업 산출물 검증

### Manifest

- **위치**: `{archive_name}.manifest.json` (archive와 동일 디렉터리)
- **필드**: `backup_at`, `source`, `archive_name`, `record_count`, `checksum`
- **용도**: 복구 시 검증 및 감사

### Checksum

- **알고리즘**: SHA-256 (`checksum.py` → `calculate_sha256`)
- **대상**: 생성된 tar.gz 파일
- **저장**: manifest의 `checksum` 필드

### Restore 절차 (운영자 복구)

운영자가 백업에서 복구할 때:

1. **아카이브 확인**: `backup_root / {archive_name}` (`.tar.gz`) 존재 확인
2. **Manifest 확인**: `{archive_name}.manifest.json` 읽어 `source`, `record_count`, `checksum` 확인
3. **Checksum 검증** (권장): `calculate_sha256(archive_path)` 결과가 manifest.checksum과 일치하는지 확인
4. **복원**:  
   - CLI: `tar -xzf {archive_path} -C {복원_대상_디렉터리}`  
   - Python: `tarfile.open(archive_path, 'r:gz').extractall(복원_대상_디렉터리)`
5. **복원 후**: 필요 시 manifest의 `source` 경로로 파일 이동/병합

### 실패/예외 처리 규칙

- **BackupManager.run()**: 예외 시 상위로 전파. 호출부(`run_maintenance_automation` 등)에서 catch 후 `status=backup_failed`, `error=str(e)` 로 구조화 반환 및 로깅.
