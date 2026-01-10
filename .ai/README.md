[Optimized: 2026-01-09]

# AI System Directory

## Purpose
- HR Agent 기반 Role Onboarding 시스템

## Structure
### agents/
- `hr.agent.md` - HR Agent 정의
  - 역할: 조직 내 Role 기준 판단 전담
  - 입력: Task 문서
  - 출력: Report 문서
  - 판단 범위: L1(Junior), L2(Senior), PENDING

### skills/
- `hr_onboarding.skill.md` - Task 문서 구조 검증
- `hr_level_check.skill.md` - Level 판단 수행
- `hr_report_emit.skill.md` - Report 생성

## Execution Flow
1. Task 문서 입력
2. HR_Onboarding_Init → 구조 검증
3. HR_Level_Check → Level 판단
4. HR_Report_Emit → Report 생성

## Meta Data Handling
- Meta 섹션: 문서 관리용
- 판단 로직: Task 본문만 사용

## Constraints
- 기준 문서 생성/수정 금지 ❌
- Task 외 추론 금지 ❌
- Meta 정보 해석 금지 ❌
