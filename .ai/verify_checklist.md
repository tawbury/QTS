# AI Code Verification Checklist

> **Purpose**: A structured audit tool for non-developers to verify AI-generated code for stability, consistency, and logical integrity.

---

## How to Use This Checklist

This checklist is designed for project managers, orchestrators, or anyone reviewing AI-generated code without deep programming expertise.

### Usage with Cursor / Claude Code

1. **Reference this file** in your chat by typing `@verify_checklist.md`
2. **Copy-paste** the relevant audit questions directly into your conversation
3. **Demand explanations** — the AI should answer in plain language, not jargon
4. **Escalate** if answers are vague, circular, or overly technical without clarification

### When to Use Each Section

| Section | Use When... |
|---------|-------------|
| Logical Integrity | New feature, bug fix, or any functional code change |
| Project Consistency | Any new file, function, or variable is introduced |
| Stability & Security | Code touches external APIs, user input, or sensitive data |
| Code Explainability | You don't understand *why* a change was made |
| Refactoring & Debt | Code feels complex, or the same logic appears in multiple places |

---

## 1. Logical Integrity & Edge Cases

> Does the code actually do what it claims to do, and does it handle real-world "what if" scenarios?

### Core Functionality

```
Audit: Walk me through exactly what this code does, step by step,
in plain language. Assume I have no programming background.
```

```
Audit: What is the single responsibility of this function/module?
If it does more than one thing, explain why that's acceptable.
```

```
Audit: Show me the exact input and output of this function with
a concrete example. What goes in, what comes out?
```

### Edge Case Handling

```
Audit: What happens if this function receives:
- A null or None value?
- An empty string or empty list?
- An extremely large number or dataset?
- A negative number (if applicable)?
List each case and the expected behavior.
```

```
Audit: What happens if the network request fails, times out,
or returns an unexpected response? Show me the error handling path.
```

```
Audit: What happens if a file doesn't exist, is locked,
or has incorrect permissions? How does the code recover?
```

```
Audit: Are there any "silent failures" where the code continues
running but produces incorrect results? Identify all such scenarios.
```

### Boundary Conditions

```
Audit: What are the minimum and maximum valid inputs for this function?
What happens at those boundaries?
```

```
Audit: If this code runs in a loop, what prevents infinite loops?
What is the termination condition?
```

```
Audit: If this function is called twice in rapid succession,
does it behave correctly? Are there race conditions?
```

---

## 2. Project Consistency (The "Glue" Check)

> Does the new code feel like it belongs in this project, or does it look like it was dropped in from somewhere else?

### Naming Conventions

```
Audit: List all new variable names, function names, and class names
you've introduced. Do they follow the existing naming patterns in this project?
Show me 3 similar examples from the existing codebase for comparison.
```

```
Audit: Are you using snake_case, camelCase, or PascalCase?
Verify this matches the project's established convention by showing existing examples.
```

```
Audit: For any abbreviations used (e.g., 'cfg', 'ctx', 'mgr'),
are these same abbreviations used elsewhere in the project?
If not, use the full word or the project's preferred abbreviation.
```

### File Structure & Organization

```
Audit: Why did you place this code in [specific file/folder]?
Show me similar functionality in the project and where it lives.
```

```
Audit: Does this new file follow the project's file naming convention?
List 5 existing files in the same directory for comparison.
```

```
Audit: If you created a new module or folder, does it follow
the project's established directory structure? Justify the location.
```

### Integration with Existing Code

```
Audit: What existing functions, classes, or utilities could have been
reused instead of writing new code? If none exist, explain why.
```

```
Audit: Show me the import statements. Are you importing from
the expected locations based on project conventions?
```

```
Audit: Does this code use the project's established patterns for:
- Configuration access
- Logging
- Error handling
- Database connections
Show the project's existing patterns and confirm alignment.
```

### Global State & Configuration

```
Audit: Does this code read from or write to any global variables,
environment variables, or configuration files? List all of them.
```

```
Audit: If you're accessing configuration, are you using the project's
existing config access pattern? Show me the standard pattern and your usage.
```

---

## 3. Stability & Security

> Could this code cause crashes, data leaks, or security vulnerabilities?

### Secrets & Sensitive Data

```
Audit: Does this code contain any hardcoded:
- API keys or tokens
- Passwords or credentials
- Database connection strings
- URLs with embedded credentials
List each occurrence or confirm none exist.
```

```
Audit: How are secrets and credentials accessed in this code?
Are they loaded from environment variables or a secure config system?
```

```
Audit: Does this code log, print, or expose any sensitive data
(even accidentally in error messages)? Check all logging statements.
```

### Input Validation

```
Audit: What user-provided or external input does this code accept?
For each input, show me the validation that prevents malicious data.
```

```
Audit: Could this code be vulnerable to:
- SQL injection (if database queries are involved)
- Command injection (if shell commands are executed)
- Path traversal (if file paths are constructed from input)
For each risk, show the protective measure or confirm it's not applicable.
```

```
Audit: Are there any places where input is directly concatenated
into strings for queries, commands, or file paths? Flag each instance.
```

### Resource Management

```
Audit: Does this code open any files, database connections,
network sockets, or external resources? Show me where each is
explicitly closed or released.
```

```
Audit: If this code runs continuously or repeatedly, will it
accumulate memory over time? Identify any lists, caches, or
data structures that grow without bounds.
```

```
Audit: Are there any background tasks, timers, or threads started
by this code? How are they properly stopped or cleaned up?
```

### Error Handling & Recovery

```
Audit: What exceptions or errors can this code throw?
For each, explain: (a) what triggers it, (b) how it's caught,
(c) what happens to the system state after the error.
```

```
Audit: If this code fails midway through an operation, is the system
left in an inconsistent state? Describe any partial failure scenarios.
```

```
Audit: Are there any "catch-all" exception handlers that might
swallow important errors silently? Show me each try/except block.
```

---

## 4. Code Explainability (Non-Developer Accessibility)

> Can the AI explain its choices in a way that a project manager can understand and challenge?

### The "Why" Behind Decisions

```
Audit: Why did you choose this specific approach over alternatives?
What other options did you consider and why were they rejected?
```

```
Audit: Explain this code change as if you were telling a colleague
who will maintain it in 6 months. What's the core intent?
```

```
Audit: Is there any "magic" in this code — values, formulas, or logic
that wouldn't be obvious to someone reading it for the first time?
Explain each magic element.
```

### Business Logic Translation

```
Audit: Translate this code into a plain-English business rule.
For example: "When X happens, the system does Y, unless Z is true."
```

```
Audit: What business requirement does this code fulfill?
Point me to the task or requirement it addresses.
```

```
Audit: If the business logic changes (e.g., a threshold value changes),
where exactly in the code would that modification be made?
```

### Documentation Check

```
Audit: Are there any comments in this code? For each comment,
does it explain WHY the code does something, not just WHAT it does?
```

```
Audit: If this code has no comments, is it truly self-explanatory?
Identify any sections that a new team member might find confusing.
```

```
Audit: Does this code have a docstring or header comment explaining
its purpose, inputs, outputs, and any important caveats?
```

---

## 5. Refactoring & Technical Debt

> Is the code clean and maintainable, or is it becoming tangled spaghetti?

### Duplication & DRY Principle

```
Audit: Is there any duplicated logic in this code?
Show me any blocks of code that appear more than once,
even with minor variations.
```

```
Audit: Is there existing code elsewhere in the project that does
something similar to what you've written? Should these be consolidated?
```

```
Audit: Are there any "copy-paste with slight modifications" patterns?
These are often signs of code that should be refactored into a shared function.
```

### Complexity Assessment

```
Audit: How deeply nested is this code? If there are more than
3 levels of indentation, explain why and whether it can be simplified.
```

```
Audit: How long is this function? If it's more than ~50 lines,
should it be broken into smaller, more focused functions?
```

```
Audit: How many parameters does this function take? If more than 4-5,
consider whether some should be grouped into a configuration object.
```

### Code Smells

```
Audit: Are there any TODO, FIXME, or HACK comments in this code?
List each one and explain whether it represents unfinished work.
```

```
Audit: Are there any "temporary" solutions that might become permanent?
Identify any shortcuts taken that should be revisited.
```

```
Audit: Is there any dead code — functions, variables, or imports
that are defined but never used? List all such items.
```

### Maintainability

```
Audit: If I need to modify this code in 6 months, what would I need
to understand first? What are the dependencies and prerequisites?
```

```
Audit: Is this code testable in isolation? Can its core logic be
tested without complex setup or external dependencies?
```

```
Audit: What would break if someone removed or renamed
[specific function/variable]? Trace the dependencies.
```

---

## 6. Quick Verification Commands

> Copy-paste these for rapid spot-checks during development.

### Fast Sanity Check

```
Quick Check: Summarize in 3 bullet points:
1. What this code does
2. What could go wrong
3. What assumptions it makes
```

### Pre-Commit Verification

```
Pre-Commit Check: Before I commit this change, confirm:
- [ ] No hardcoded secrets or credentials
- [ ] All error cases are handled
- [ ] Code follows project naming conventions
- [ ] No TODO/FIXME items left unaddressed
- [ ] All new functions have clear single responsibilities
```

### Integration Check

```
Integration Check: How does this change affect:
1. Other parts of the codebase that call this code
2. Configuration or environment requirements
3. Test coverage — are there tests for this change?
```

---

## Appendix: Red Flags Glossary

| Term | What It Means | Why It's Bad |
|------|---------------|--------------|
| **Hardcoded value** | A specific number or string directly in code | Hard to change, often leads to bugs |
| **Magic number** | An unexplained numeric constant | Nobody knows why it's that value |
| **Silent failure** | Code that fails but doesn't report it | Bugs hide and data corrupts |
| **Race condition** | Timing-dependent bugs | Works sometimes, fails randomly |
| **Memory leak** | Resources that pile up over time | System slows down and crashes |
| **Spaghetti code** | Tangled, hard-to-follow logic | Maintenance nightmare |
| **Dead code** | Code that's never executed | Confusion and clutter |
| **Catch-all exception** | Catching every error without handling | Bugs get hidden |

---

## Checklist Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-31 | Initial checklist created |

---

*This checklist is a living document. Update it as new patterns, issues, or verification needs emerge.*
