[Optimized: 2026-01-09]

# HR Level Check Skill

## Core Logic
- Task 본문 기준 Level 판단
- 결과: L1 | L2 | PENDING

## Input/Output
### Input
- Task 문서 내용 (Meta section 제외)

### Output
- Level Result (L1/L2/PENDING)
- Decision Basis Summary

## Decision Rules
### Common Criteria
- **L1 (Junior):** 지도/감독 필요, 학습 중, 제한된 책임
- **L2 (Senior):** 독립적 수행, 멘토링, 복잡한 문제 해결, 의사결정권

### Department Keywords
- **Dev:** L2=아키텍처 설계, 기술 부채 관리, 코드 리뷰 주도 | L1=기능 구현, 버그 수정
- **Content:** L2=전략 수립, 브랜드 가이드라인 제정, 파이프라인 최적화 | L1=단순 편집, 애셋 제작

### PENDING Criteria
- 기준 불명확/부족
- L1/L2 구분 모호
- 판단 정보 부족
- 모호/일반적 기술만 존재

## Judgment Logic
1. Task 본문 `Provided Criteria` 섹션만 분석 (Meta 제외)
2. `Department` 필드 기반 특화 키워드 가중치 적용
3. L1 기준에 가까우면 L1 판정
4. L2 기준에 가까우면 L2 판정
5. 명확하지 않으면 PENDING 판정

## Constraints
- Task 본문 기준 ONLY
- Meta 정보 사용 절대 금지
- L1/L2/PENDING 결과만 허용
- 추론/가정 금지

## Return Format
```
Level: L1|L2|PENDING
Basis: [판단 근거 요약]
```
