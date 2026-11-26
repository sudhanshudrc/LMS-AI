# LMS-AI Platform

An enterprise-grade, AI-native Learning Management System backend engineered with FastAPI, PostgreSQL, SQLAlchemy 2.0 (async), structlog observability, and modern AI engineering patterns.

---

## 1. Executive Summary

LMS-AI is designed to transform self-paced video and curriculum learning into an adaptive, multimodal experience. Built around a **Course-First** structural model inspired by modern Open edX architecture, the platform features:
- **Clean Architecture & 3-Tier Layering**: Explicit decoupling across HTTP Routers, Domain Services, and Database Repositories.
- **Production Observability**: Full structured JSON logging powered by `structlog` with correlation ID (`X-Correlation-Id`) tracing and User ID context binding.
- **Interactive AI Readiness**: Video transcripts with second-accurate timestamped cues (`JSONB`) and full continuous text indexed with PostgreSQL `GIN` full-text search.
- **Frictionless Learning**: Immediate open access to course catalogs and content with automatic granular tracking for video playback and module completions.

---

## 2. Platform Architecture

```
                       ┌──────────────────────────────┐
                       │       Client / Frontend      │
                       └──────────────┬───────────────┘
                                      │ HTTP (X-Correlation-Id, X-User-Id)
                                      ▼
                       ┌──────────────────────────────┐
                       │   RequestLoggingMiddleware   │
                       │   (structlog contextvars)    │
                       └──────────────┬───────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
┌──────────────┐              ┌──────────────┐              ┌──────────────┐
│ Course Route │              │Content Route │              │Progress Route│
└───────┬──────┘              └───────┬──────┘              └───────┬──────┘
        │                             │                             │
        ▼                             ▼                             ▼
┌──────────────┐              ┌──────────────┐              ┌──────────────┐
│Course Service│              │ContentService│              │ProgressServic│
└───────┬──────┘              └───────┬──────┘              └───────┬──────┘
        │                             │                             │
        ▼                             ▼                             ▼
┌──────────────┐              ┌──────────────┐              ┌──────────────┐
│  Course Repo │              │ Content Repo │              │Progress Repo │
└───────┬──────┘              └───────┬──────┘              └───────┬──────┘
        └─────────────────────────────┼─────────────────────────────┘
                                      ▼
                       ┌──────────────────────────────┐
                       │  PostgreSQL 16 (AsyncPG)     │
                       │  - GIN Full-Text Indexes     │
                       │  - Timed Cues JSONB          │
                       │  - Async Connection Pool     │
                       └──────────────────────────────┘
```

---

## 3. Core AI Features Under Development

The platform is purpose-built to deliver five student-facing AI capabilities operating over the base curriculum and transcript foundation:

### Feature 1: SchedulAI (Smart Study Scheduling)
- **Problem Solved**: Students often struggle with time management, resulting in cramming, dropped courses, and inconsistent study habits.
- **Core Capability**: Constructs dynamic, personalized study timetables tailored to individual deadlines, target weekly hours, and course structure. SchedulAI proactively calculates workload density, monitors streak counters, awards study points, and automatically reschedules missed sessions without overwhelming the learner.
- **Primary Inputs**: User target completion date, available study hours per week, module/item counts, and completion states.
- **Primary Outputs**: Adaptive study timetable, milestone alerts, streak/point metrics, and reschedule event plans.

### Feature 2: Auto-Generated Flashcards & Revision
- **Problem Solved**: Passive video consumption leads to low retention and weak conceptual recall over time.
- **Core Capability**: Automatically extracts core definitions, formulas, and concepts from lecture transcripts and Markdown notes. Generates active-recall flashcard decks powered by spaced-repetition algorithms (Leitner system / SM-2) to ensure long-term retention.
- **Primary Inputs**: Section ID, module ID, lecture transcripts, and study notes.
- **Primary Outputs**: Structured flashcard decks (question, answer, difficulty, Leitner box level, review schedule).

### Feature 3: Personalized Pictorial Understanding
- **Problem Solved**: Complex algorithmic, architectural, and data structure topics can be difficult to grasp from verbal lectures alone.
- **Core Capability**: Diagnoses student misconceptions through targeted diagnostic probes and quiz evaluation. Generates tailored visual diagrams (Mermaid, SVG, ASCII workflows) accompanied by intuitive analogies to clarify difficult concepts.
- **Primary Inputs**: Section context, learner questions, failed quiz attempts, lecture transcript snippets.
- **Primary Outputs**: Misconception diagnostic analysis, tailored diagram specifications (Mermaid/SVG), and simplified analogies.

### Feature 4: Podcast Generator
- **Problem Solved**: Busy students cannot always look at a screen while commuting or exercising, limiting opportunities for learning.
- **Core Capability**: Transforms dense lecture transcripts, summaries, and Markdown notes into an engaging, multi-speaker audio podcast dialogue. Two AI co-hosts discuss key concepts, unpack tricky ideas, debate nuances, and summarize major takeaways.
- **Primary Inputs**: Section or module transcripts, key concepts, target audio duration (e.g. 5 min, 10 min).
- **Primary Outputs**: Two-speaker conversational script (`Host A`, `Host B`), synthesizable audio timeline markers, and audio output files.

### Feature 5: Slide Deck Generator
- **Problem Solved**: Learners need concise, visual, and portable summaries to review before exams and technical interviews.
- **Core Capability**: Synthesizes course materials into structured presentation slide decks formatted in Marp or Reveal.js Markdown, highlighting bullet points, syntax-highlighted code snippets, and architectural breakdowns.
- **Primary Inputs**: Course, module, or section transcripts, study guides, and content metadata.
- **Primary Outputs**: Presentation-ready slide deck JSON, exportable Marp/Markdown files, and downloadable decks.

---

## 4. Correlation ID & User ID Observability Architecture

LMS-AI implements two-dimensional logging where every request couples a technical trace with an identity trace:

1. **`correlation_id` (`X-Correlation-Id`)**: Unique identifier for every individual HTTP transaction. Injected into `structlog.contextvars` by the `RequestLoggingMiddleware`, propagated across async boundaries, and returned in client response headers.
2. **`user_id` (`X-User-Id`)**: Identifier representing the authenticated learner.

### Why This Coupling Matters
- **Millisecond Triage**: When a user experiences an issue, their response header provides the incident `correlation_id`. Support can immediately isolate the exact 5 to 10 log statements for that specific transaction out of millions.
- **Dual Query Capability**:
  - `user_id == "usr_123"`: Traces a learner's complete chronological journey across courses and days.
  - `correlation_id == "req_abc"`: Traces the exact database queries, service validations, and external AI calls for a single failing transaction.
- **AI Latency & Token Auditing**: Automatically attributes token consumption, prompt costs, and API latency to specific users while monitoring performance across RAG pipelines.

---

## 5. Technology Stack

- **Language**: Python 3.12+
- **Framework**: FastAPI (Async)
- **Data Validation & Schemas**: Pydantic V2 & `pydantic-settings`
- **Database**: PostgreSQL 16
- **ORM & Driver**: SQLAlchemy 2.0 (Declarative Async) with `asyncpg` and `greenlet`
- **Package & Environment Manager**: `uv`
- **Containerization**: Docker & Docker Compose
- **Logging & Tracing**: `structlog` with ContextVars correlation tracking
- **Testing**: `pytest`, `pytest-asyncio`, `httpx`
- **Static Analysis & Linting**: `ruff`, `pyright`

---

## 6. Project Layout

```
LMS-AI/
├── context/                              # Architecture documentation & developer guides
│   ├── api_developer_guide.md            # Detailed API documentation
│   └── schema_guide.md                   # PostgreSQL schema and table designs
├── data/                                 # Datasets (Curriculum Excel & Transcripts)
├── plan/                                 # Engineering implementation plans
├── scripts/                              # Maintenance and database seeding scripts
│   ├── init_and_seed.py                  # Database initialization and seeding
│   └── schema.sql                        # Base DDL
├── src/                                  # Application source code
│   └── app/
│       ├── ai/                           # AI modules (Agents, Embeddings, Prompts)
│       ├── api/                          # HTTP layer
│       │   ├── health.py                 # Health and readiness endpoints
│       │   └── v1/                       # API v1 routes, schemas, and services
│       │       ├── routes/               # FastAPI route definitions
│       │       ├── schemas/              # Pydantic request/response models
│       │       └── services/             # Business logic layer
│       ├── constants/                    # Enums, tables, messages
│       ├── core/                         # Config, security, structlog, middleware
│       ├── db/                           # SQLAlchemy engine, models, and repositories
│       │   ├── models/                   # Declarative ORM models
│       │   ├── repositories/             # Database access layer
│       │   └── session.py                # Async session management
│       └── main.py                       # Application entrypoint & lifespan
├── tests/                                # Test suite (Unit, Core, DB, API)
├── Dockerfile                            # Production multi-stage Docker build
├── docker-compose.yml                    # Local orchestration (FastAPI + PostgreSQL)
├── pyproject.toml                        # Project dependencies and tool configurations
└── README.md                             # This file
```

---

## 7. Getting Started

### Prerequisites
- Docker & Docker Compose (v2+)
- Python 3.12+ (if developing locally)
- `uv` (recommended package installer)

### Quick Start with Docker

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd LMS-AI
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   ```

3. **Start PostgreSQL and FastAPI**:
   ```bash
   docker compose up --build -d
   ```

4. **Verify Health Endpoints**:
   ```bash
   curl -i http://localhost:8000/health
   curl -i http://localhost:8000/health/db
   ```

5. **Access Interactive API Docs**:
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Local Development Setup

1. **Create and Activate Virtual Environment**:
   ```bash
   uv venv
   source .venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   uv sync
   ```

3. **Start PostgreSQL**:
   ```bash
   docker compose up -d postgres
   ```

4. **Initialize and Seed Database**:
   ```bash
   python scripts/init_and_seed.py
   ```

5. **Run Application**:
   ```bash
   uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Run Test Suite**:
   ```bash
   pytest -v
   ```

---

## 8. Development & Contribution Standards

All contributors must adhere to the project standards defined in [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md):
- **Strict No-Emoji Policy**: No emojis in code, comments, docstrings, commits, or documentation.
- **4-Stage Verification Gate**: Every modification must pass linting (`ruff`), type checking (`pyright`), error handling standards, and unit/integration tests before merging.
- **Layer Separation**: HTTP routes must never import database repositories directly; all interactions must pass through domain services.
