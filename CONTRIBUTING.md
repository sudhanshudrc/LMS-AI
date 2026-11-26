# Contributing to LMS-AI

Thank you for your interest in contributing to the LMS-AI platform. This document outlines the technical standards, architectural rules, Git workflows, and verification procedures required for all contributions.

---

## 1. Core Principles & Non-Negotiable Rules

Before writing any code or documentation, review these platform-wide mandates:

### Strict No-Emoji Policy
**Do not use emojis anywhere.** This applies universally across the entire project:
- Source code, comments, docstrings, and type annotations
- Markdown files, documentation, and guides
- Commit messages, pull request titles, and descriptions
- Terminal and logging messages
- Test names and assertion messages

### Clean Architecture & Layer Separation
We enforce a strict 3-tier layering model:
- **Routes (`src/app/api/v1/routes/`)**: Handle HTTP serialization, status codes, query/path parameters, and caller authentication. Routes **MUST NEVER** import or interact with database repositories directly.
- **Services (`src/app/api/v1/services/`)**: Implement business logic, permission checks, data transformations, and orchestrate repository calls.
- **Repositories (`src/app/db/repositories/`)**: Encapsulate all database queries, filtering, and database mutations using SQLAlchemy async sessions.

### Observability & Correlation Tracing
- All logging must use `structlog.get_logger()`. Do not use standard library `logging.getLogger()` directly.
- Never write `print()` statements in application code.
- Contextual variables (`correlation_id`, `user_id`, `path`, `method`) are bound automatically via ContextVars. When logging events inside services, log structured key-value pairs:
  ```python
  logger.info("course_retrieved", course_id=course_id, sections_count=len(sections))
  ```

---

## 2. Git Branching & Collaboration Model

To enable multiple developers to build features concurrently without conflicts:

### Branch Naming Conventions
- `feature/<feature-name>`: New capabilities (e.g. `feature/schedulai-engine`, `feature/flashcard-generation`).
- `fix/<issue-description>`: Bug fixes (e.g. `fix/transcript-cue-parsing`).
- `refactor/<target>`: Architectural or performance refactoring without behavioral changes.
- `docs/<subject>`: Documentation updates.

### Feature Isolation Rule
- Features may depend on shared infrastructure (`src/app/core/`, `src/app/db/`, `src/app/constants/`).
- Features **must not depend directly on other parallel features**. Shared models or events must be defined in the core layers.

---

## 3. Mandatory 4-Stage Post-Code Verification Gate

Every change must successfully pass through this 4-stage filter before opening a pull request or merging:

```
[ Code Modified / Created ]
            │
            ▼
┌────────────────────────────────────────────────────────┐
│  Stage 1: Anti-Patterns & Code Style                   │
│  - Run ruff check and verify PEP 8 compliance          │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Stage 2: Type Safety & Contract Integrity             │
│  - Strict type hints on all signatures                 │
│  - Pydantic V2 idioms and Pyright / Mypy validation    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Stage 3: Error Handling & Resilience                  │
│  - Domain exceptions inheriting from AppError          │
│  - Explicit timeouts and async resource safety         │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Stage 4: Tests & Systematic Debugging                 │
│  - pytest suite passing with zero regressions          │
│  - Root-cause analysis for any test failures           │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
                 [ Ready for PR / Merge ]
```

### Verification Checklist
1. **Stage 1: Static Hygiene & Anti-Patterns**
   - [ ] No mutable default arguments (`def func(items=[]):`).
   - [ ] No bare `except:` or catching raw `Exception` without re-raising or logging.
   - [ ] No blocking I/O calls inside async coroutines (e.g. `requests.get` inside `async def`).
   - [ ] Imports sorted and unused variables removed.

2. **Stage 2: Type Safety & Contracts**
   - [ ] All functions, methods, and route handlers have explicit parameter and return type hints.
   - [ ] Modern Python 3.12+ type union syntax used (`int | None` instead of `Optional[int]`).
   - [ ] API endpoints return typed `ApiResponse[T]` contracts.

3. **Stage 3: Error Handling & Resilience**
   - [ ] Custom domain errors inherit from `src.app.core.exceptions.AppError`.
   - [ ] Network, external API, and database calls have explicit timeouts.
   - [ ] Batch operations isolate individual item failures.

4. **Stage 4: Automated Testing**
   - [ ] Unit and integration tests added or updated under `tests/`.
   - [ ] Entire test suite passes cleanly: `pytest -v`.

---

## 4. Local Development Workflow

### Setting Up Your Environment
```bash
# 1. Clone repository
git clone <repo-url>
cd LMS-AI

# 2. Create virtual environment using uv
uv venv
source .venv/bin/activate

# 3. Synchronize dependencies
uv sync

# 4. Start database in background
docker compose up -d postgres

# 5. Run database migration and seed data
python scripts/init_and_seed.py
```

### Running Checks Locally
Run these commands before submitting any pull request:

```bash
# Format check and linting
ruff check src/ tests/

# Type checking
pyright src/

# Test suite execution
pytest -v
```

---

## 5. Commit Message Conventions

Commit messages must be clear, concise, imperative, and contain no emojis. Follow the Conventional Commits format:

```
<type>(<scope>): <short description in present tense>

[optional body explaining what and why]
```

### Allowed Types
- `feat`: A new user-facing or API feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Code change that improves performance
- `test`: Adding or correcting tests
- `chore`: Build process, dependencies, or auxiliary tool changes

### Examples
- `feat(api): implement course curriculum tree endpoint`
- `fix(content): resolve missing greenlet error on video content types`
- `refactor(logging): integrate structlog with contextvars correlation id`
- `docs(context): document api endpoints and developer integration guide`
