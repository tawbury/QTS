[Optimized: 2026-01-09]

# HR Onboarding Init Skill

## Core Logic
- Task 문서 구조 검증
- 필수 항목 누락 확인

## Input/Output
### Input
- Task 문서 경로 또는 내용

### Output
- Validation Result (PASS/FAIL)
- Missing Fields List (if any)

## Validation Rules
### Required Meta Fields
- Project Name, File Name, Document ID, Status
- Created Date, Last Updated, Author, Parent Document

### Required Content Sections
- Department, Role Name, Expected Level
- Provided Criteria, Notes

### Structural Requirements
- Meta section 존재 및 정확한 포맷
- Content separator (`---`) 존재
- 모든 필수 섹션과 적절한 헤더

## Validation Logic
1. Meta section 완전성 검사
2. 모든 필수 content 섹션 존재 확인
3. Section header format 검증 (##)
4. 필수 필드 비어있지 않음 확인
5. 모든 검사 통과 시 PASS 반환
6. 검사 실패 시 FAIL + 누락 필드 목록 반환

## Constraints
- 판단 수행 금지
- 내용 기반 평가 금지
- 구조 검증 ONLY
- 부수적 효과 없음

## Return Format
```
Status: PASS|FAIL
Missing Fields: [field1, field2, ...] (if FAIL)
```
