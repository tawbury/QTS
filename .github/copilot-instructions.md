# Copilot Instructions for QTS Repository

## Big Picture Architecture
- QTS is organized by phases, each representing a major architectural or workflow milestone. See `docs/tasks/README.md` for phase breakdowns and status.
- Core logic is in `src/` (ops, runtime, shared), with configuration in `config/` and documentation in `docs/`.
- Observer is a **separate project**; this repo does not contain Observer implementation. QTS consumes Observer outputs at ETEDA pipeline (snapshot), Decision pipeline (context), and Retention (dataset_root). See `docs/tasks/phases/Phase_00_Observer/Observer_Boundary.md`.
- Data flows from runtime and ops modules, with reporting to `docs/reports/`. Observer dataset paths (e.g. `config/observer/`) are provided by deployment/config when used.

## Developer Workflows
- Tasks are managed in `docs/tasks/` using templates. Automated workflows:
  1. Generate task file in `docs/tasks/`.
  2. Validate structure with `HR_Onboarding_Init` logic.
  3. Judge level with `HR_Level_Check` (keywords: Dev/Content).
  4. Emit report to `docs/reports/`.
- Reports must use the structure in `hr_report_emit.skill.md` and include a Feedback for Improvement section.
- All user inputs, task definitions, and instructions must be in English. All conversational responses to users must be in Korean. Reports in `docs/reports/` must be in English and machine-readable.

## Project-Specific Conventions
- Directory and file naming follows `<role>_<dept>` for tasks and reports.
- Meta section data (e.g., Expected Level) must not influence evaluation results.
- If criteria are insufficient, set status to `PENDING` and provide detailed feedback.
- No natural language in reports; use structured, deterministic formats.
- In case of language conflict, follow the Language & Output Policy in `.ai/.cursorrules`.

## Integration Points & Patterns
- Agent context and workflow are defined in `agents/hr/hr.agent.md`.
- Document templates and constraints are in `.ai/.cursorrules`.
- Data contracts and architecture specs are in `docs/arch/` and `docs/spec/`.
- Observer outputs (when integrated) are under a configurable path; see Observer_Boundary.md. This repo does not ship `config/observer/` by default.

## Key Files & Directories
- `src/` – main codebase (ops, runtime, shared)
- Observer dataset path – configurable at deploy time (see Observer_Boundary.md)
- `docs/tasks/` – phase/task management
- `docs/reports/` – evaluation outputs
- `.ai/.cursorrules` – agent rules and language policy
- `agents/hr/hr.agent.md` – agent workflow context
- `docs/arch/` and `docs/spec/` – architecture and contract documentation

## Example Patterns
- To add a new task: create `docs/tasks/task_<role>_<dept>.md` using the template, validate, and emit report.
- To generate a report: follow the deterministic structure, write in English, and save to `docs/reports/report_<role>_<dept>_<YYYYMMDD>.md`.
- For agent logic, always refer to `.ai/.cursorrules` for constraints and language policy.

---
For further details, see referenced files and templates. If any section is unclear or incomplete, please provide feedback for iteration.