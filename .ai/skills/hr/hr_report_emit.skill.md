[Optimized: 2026-01-09]

# HR Report Emit Skill

## Core Logic
- 판단 결과 → 구조화된 Report 출력
- 다른 Agent 소비용 문서 생성

## Input/Output
### Input
- Task 문서 정보 (role, department, meta)
- Level 판단 결과 (L1/L2/PENDING)
- Decision basis 정보

### Output
- 구조화된 Report 문서

## Report Structure
### Meta Section
- Project Name: [from task]
- File Name: report_<role>_<dept>_<date>.md
- Document ID: <Project>-REPORT-<number>
- Status: Active
- Created Date: YYYY-MM-DD HH:MM
- Author: HR Agent
- Parent Document: [[task_<role>_<dept>.md]]
- Related Reference: [blank]

### Content Sections
- Role: [role name]
- Department: [department name]
- Evaluation Result: Status: L1|L2|PENDING
- Decision Basis:
  - Matched Criteria: [list]
  - Missing/Unclear Criteria: [list]
- Flags: Needs Review: true|false
- Feedback for Improvement:
  - Action Items: [PENDING 시 사용자 추가 내용]
  - Recommended Keywords: [직군 권장 역량 키워드]

## Generation Rules
1. File name: report_<role>_<dept>_<YYYYMMDD>.md
2. Meta section 템플릿 정확히 준수
3. Evaluation Result: status 값만 포함
4. Decision Basis: matched/missing 리스트 분리
5. Needs Review = true IF PENDING OR 불명확 기준
6. Needs Review = false IF 명확한 L1/L2 결정

## Output Format
```markdown
# HR Evaluation Report

## Meta
[meta section template]

---

## Role
- [role]

## Department  
- [department]

## Evaluation Result
- Status : L1|L2|PENDING

## Decision Basis
### Matched Criteria
- [criteria1]
- [criteria2]

### Missing / Unclear Criteria
- [criteria1]
- [criteria2]

## Flags
- Needs Review : true|false
```

## Constraints
- 구조화된 데이터만 출력
- 자연어 설명 금지
- Agent 소비용 포맷 준수
- 결정론적 구조 유지
