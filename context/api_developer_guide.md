# LMS-AI Platform: API Developer & Integration Guide

This document is the authoritative developer reference for all available HTTP endpoints in the LMS-AI backend. It explains the request requirements, expected response envelopes, HTTP status codes, and practical usage examples so developers can integrate frontend components and build the 5 AI features without ambiguity.

---

## 1. Global Conventions & Standards

### 1.1 Base URL & Environment
- **Local / Docker API URL**: `http://localhost:8000`
- **Prefix for all v1 endpoints**: `/api/v1`
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`
- **Raw OpenAPI Schema**: `http://localhost:8000/openapi.json`

### 1.2 Unified Response Envelope
Every response returned by this API is wrapped inside a uniform `ApiResponse[T]` envelope:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully.",
  "errors": null
}
```

When an error occurs (such as a 400, 401, 404, or 500), the envelope format remains identical:

```json
{
  "success": false,
  "data": null,
  "message": "The requested course was not found.",
  "errors": null
}
```

### 1.3 Headers & Authentication
- **Correlation ID**: Every incoming request accepts an optional `X-Correlation-Id` header (UUID string). If omitted, the server automatically generates one and returns it in the response headers.
- **Learner Identity**: Endpoints that operate in the context of a learner (such as `/progress` endpoints) expect the user's UUID in the `X-User-Id` header:
  ```http
  X-User-Id: 0b6c9f2e-1d3a-4f6b-8a2c-5e7d9f1b3c4a
  ```
  If this header is missing on protected routes, the server returns `401 Unauthorized` with message `"Authentication credentials were not provided or are invalid."`.

---

## 2. API Endpoint Directory

```
LMS-AI Platform API
│
├── System & Health Probes
│   ├── GET /health
│   └── GET /health/db
│
├── Course Catalog & Curriculum Tree
│   ├── GET /api/v1/courses
│   ├── GET /api/v1/courses/{identifier}
│   └── GET /api/v1/courses/{course_id}/tree
│
├── Content Delivery & Transcripts
│   ├── GET /api/v1/items/{item_id}/content
│   ├── GET /api/v1/items/{item_id}/transcript
│   └── GET /api/v1/transcripts/search
│
└── Learner Progress Tracking
    ├── GET  /api/v1/progress/courses/{course_id}
    ├── POST /api/v1/progress/items/{item_id}/playback
    └── POST /api/v1/progress/items/{item_id}/complete
```

---

## 3. Detailed Endpoint Specifications

### 3.1 System & Health Probes

#### `GET /health`
Returns application liveness and deployment environment. Used by Docker health checks and load balancers.
- **Authentication**: None.
- **Request Parameters**: None.
- **Response `data`**:
  ```json
  {
    "status": "healthy",
    "service": "lms-ai-api",
    "environment": "production"
  }
  ```

#### `GET /health/db`
Verifies that the PostgreSQL async connection pool is operational by issuing a `SELECT 1` ping.
- **Authentication**: None.
- **Request Parameters**: None.
- **Response `data`**:
  ```json
  {
    "database": "connected",
    "pool_connected": true
  }
  ```

---

### 3.2 Course Catalog & Curriculum Tree

#### `GET /api/v1/courses`
Lists all published courses with pagination.
- **Authentication**: None.
- **Query Parameters**:
  - `offset` (integer, default `0`, min `0`): Number of items to skip.
  - `limit` (integer, default `20`, min `1`, max `100`): Page size.
- **Example Request**:
  ```http
  GET /api/v1/courses?limit=2&offset=0
  ```
- **Response `data`**:
  ```json
  {
    "items": [
      {
        "id": "e69509e4-d4b3-4c89-a15c-c42cf12ea84d",
        "org": "Neso Academy",
        "course_id": "CPP-101",
        "title": "Mastering C++ Programming: From Syntax to Memory Mastery",
        "subtitle": "Complete guide to modern C++20",
        "duration": "8 weeks",
        "effort": "6-8 hours per week",
        "language": "en",
        "short_description": "Comprehensive journey into high-performance C++.",
        "is_published": true
      }
    ],
    "pagination": {
      "total_count": 5,
      "offset": 0,
      "limit": 2,
      "has_more": true
    }
  }
  ```

#### `GET /api/v1/courses/{identifier}`
Retrieves comprehensive course details and prerequisite courses. The `{identifier}` parameter accepts either a canonical course code (e.g. `CPP-101`) or a primary key UUID.
- **Authentication**: None.
- **Path Parameters**:
  - `identifier` (string, required): Course code like `CPP-101` or UUID like `e69509e4-d4b3-4c89-a15c-c42cf12ea84d`.
- **Response `data`**:
  ```json
  {
    "id": "e69509e4-d4b3-4c89-a15c-c42cf12ea84d",
    "org": "Neso Academy",
    "course_id": "CPP-101",
    "title": "Mastering C++ Programming: From Syntax to Memory Mastery",
    "subtitle": "Complete guide to modern C++20",
    "duration": "8 weeks",
    "effort": "6-8 hours per week",
    "language": "en",
    "short_description": "Comprehensive journey into high-performance C++.",
    "description": "Full syllabus details...",
    "overview": "Course outcomes and roadmap...",
    "start_date": null,
    "end_date": null,
    "is_published": true,
    "prerequisites": [
      {
        "course_id": "37ac6b17-0db2-4bc6-945e-721d4ce4a602",
        "code": "PY-101",
        "title": "Python Programming: Beginner to Software Engineering"
      }
    ]
  }
  ```
- **Error Responses**:
  - `404 Not Found`: If course code or UUID does not exist.

#### `GET /api/v1/courses/{course_id}/tree`
Returns the full recursive curriculum hierarchy (`Course -> Modules -> Sections -> SectionItems`). Essential for rendering the course sidebar and used by SchedulAI to calculate total study load.
- **Authentication**: None.
- **Path Parameters**:
  - `course_id` (UUID, required): The course primary key UUID.
- **Response `data`**:
  ```json
  {
    "id": "e69509e4-d4b3-4c89-a15c-c42cf12ea84d",
    "course_id": "CPP-101",
    "title": "Mastering C++ Programming",
    "modules": [
      {
        "id": "96f01da5-06d2-45e0-82d8-552ca2e6adfb",
        "title": "Introduction to Modern C++",
        "description": "Core paradigms and memory models",
        "order_index": 0,
        "sections": [
          {
            "id": "a823d45f-1412-4c6e-8ff9-bc421f201e91",
            "title": "Setting Up Development Environment",
            "description": null,
            "order_index": 0,
            "items": [
              {
                "id": "d13540a1-63cb-4db8-8314-e0ebaa24e868",
                "title": "Installing Clang and GCC",
                "content_type": "video",
                "order_index": 0
              },
              {
                "id": "e24681b2-74dc-4ec9-9425-f1fcbb35f979",
                "title": "Toolchain Architecture Reading",
                "content_type": "text",
                "order_index": 1
              }
            ]
          }
        ]
      }
    ]
  }
  ```

---

### 3.3 Content Delivery & Transcripts

#### `GET /api/v1/items/{item_id}/content`
Returns the polymorphic learning content for an item. The response structure adapts depending on whether the item is a video lecture or a reading document.
- **Authentication**: None.
- **Path Parameters**:
  - `item_id` (UUID, required): Section item UUID.
- **Response `data` (When Video Item)**:
  ```json
  {
    "item_id": "d13540a1-63cb-4db8-8314-e0ebaa24e868",
    "title": "Installing Clang and GCC",
    "content_type": "video",
    "video": {
      "id": "c19b380f-9273-455b-b5bc-135e5d36e2f1",
      "section_item_id": "d13540a1-63cb-4db8-8314-e0ebaa24e868",
      "video_url": "https://www.youtube.com/watch?v=example",
      "youtube_video_id": "example",
      "duration_seconds": 640,
      "thumbnail_url": "https://img.youtube.com/vi/example/maxresdefault.jpg"
    },
    "text": null
  }
  ```
- **Response `data` (When Reading Item)**:
  ```json
  {
    "item_id": "e24681b2-74dc-4ec9-9425-f1fcbb35f979",
    "title": "Toolchain Architecture Reading",
    "content_type": "text",
    "video": null,
    "text": {
      "id": "f28491c3-8392-4a1d-91b3-4628a8d1045e",
      "section_item_id": "e24681b2-74dc-4ec9-9425-f1fcbb35f979",
      "body_markdown": "# Modern Toolchains\n\nCompilers convert source code...",
      "estimated_read_time_seconds": 300
    }
  }
  ```

#### `GET /api/v1/items/{item_id}/transcript`
Retrieves the complete spoken dialogue and timed subtitle cues for a video lecture. This endpoint is the primary knowledge source used by Podcast (F4), Flashcards (F2), and Slide Deck (F5) generators.
- **Authentication**: None.
- **Path Parameters**:
  - `item_id` (UUID, required): Section item UUID.
- **Query Parameters**:
  - `language` (string, optional, default `"en"`): Target language code.
- **Response `data`**:
  ```json
  {
    "id": "9a3841e2-b482-41f2-9523-d8c91a0248e3",
    "video_content_id": "c19b380f-9273-455b-b5bc-135e5d36e2f1",
    "language_code": "en",
    "full_text": "Welcome to this lecture. Today we are going to explore...",
    "timed_cues": [
      {
        "start": 0.0,
        "end": 4.5,
        "text": "Welcome to this lecture."
      },
      {
        "start": 4.5,
        "end": 9.2,
        "text": "Today we are going to explore compilers and linkers."
      }
    ],
    "vtt_content": "WEBVTT\n\n00:00.000 --> 00:04.500\nWelcome to this lecture."
  }
  ```

#### `GET /api/v1/transcripts/search`
Searches across all video transcripts using PostgreSQL GIN full-text search and returns keyword-matching segments ranked by relevance score.
- **Authentication**: None.
- **Query Parameters**:
  - `query` (string, required): Plain text keyword query (e.g. `asymptotic analysis`, `pointers`).
  - `course_id` (UUID, optional): Filter search scope to a specific course.
  - `limit` (integer, default `10`, min `1`, max `50`): Maximum results to return.
- **Example Request**:
  ```http
  GET /api/v1/transcripts/search?query=pointers&limit=5
  ```
- **Response `data`**:
  ```json
  [
    {
      "transcript_id": "9a3841e2-b482-41f2-9523-d8c91a0248e3",
      "video_content_id": "c19b380f-9273-455b-b5bc-135e5d36e2f1",
      "language_code": "en",
      "snippet": "...pointers store memory addresses directly in C++...",
      "rank": 0.0892
    }
  ]
  ```

---

### 3.4 Learner Progress Tracking

#### `GET /api/v1/progress/courses/{course_id}`
Calculates real-time completion percentage and module breakdowns for the authenticated learner.
- **Authentication**: Requires `X-User-Id` header.
- **Path Parameters**:
  - `course_id` (UUID, required): Course UUID.
- **Response `data`**:
  ```json
  {
    "course_id": "e69509e4-d4b3-4c89-a15c-c42cf12ea84d",
    "total_items": 12,
    "completed_items": 3,
    "overall_percentage": 25.00,
    "modules": [
      {
        "module_id": "96f01da5-06d2-45e0-82d8-552ca2e6adfb",
        "status": "in_progress",
        "progress_percentage": 50.00,
        "completed_at": null
      }
    ]
  }
  ```

#### `POST /api/v1/progress/items/{item_id}/playback`
Saves video resume position so the learner can pick up where they stopped watching.
- **Authentication**: Requires `X-User-Id` header.
- **Path Parameters**:
  - `item_id` (UUID, required): Section item UUID.
- **Request Body**:
  ```json
  {
    "position_seconds": 345,
    "mark_completed": false
  }
  ```
- **Response `data`**:
  ```json
  {
    "section_item_id": "d13540a1-63cb-4db8-8314-e0ebaa24e868",
    "status": "in_progress",
    "last_playback_position_seconds": 345,
    "is_completed": false,
    "completed_at": null,
    "last_activity_at": "2026-11-26T14:15:30.123456Z"
  }
  ```

#### `POST /api/v1/progress/items/{item_id}/complete`
Idempotently marks a video or reading item as completed.
- **Authentication**: Requires `X-User-Id` header.
- **Path Parameters**:
  - `item_id` (UUID, required): Section item UUID.
- **Request Body**: Empty body `{}`.
- **Response `data`**:
  ```json
  {
    "section_item_id": "d13540a1-63cb-4db8-8314-e0ebaa24e868",
    "status": "completed",
    "last_playback_position_seconds": 640,
    "is_completed": true,
    "completed_at": "2026-11-26T14:16:00.000000Z",
    "last_activity_at": "2026-11-26T14:16:00.000000Z"
  }
  ```

---

## 4. Error Codes & Troubleshooting

| HTTP Status | Message Key | Typical Cause | Resolution |
| :--- | :--- | :--- | :--- |
| `400 Bad Request` | `REQUEST_VALIDATION_FAILED` | Query parameter broke a constraint (e.g. `limit > 100`, `offset < 0`). | Provide valid query parameters matching the bounds. |
| `401 Unauthorized` | `UNAUTHORIZED_ACCESS` | `X-User-Id` header is missing on a protected endpoint. | Supply the authenticated user's UUID in `X-User-Id`. |
| `401 Unauthorized` | `INVALID_SERVICE_TOKEN` | `X-User-Id` is not a valid UUID format or user does not exist. | Verify the UUID against registered users in the database. |
| `403 Forbidden` | `USER_INACTIVE` | The user's account has `is_active = false`. | Reactivate user account in administrative settings. |
| `403 Forbidden` | `PERMISSION_DENIED` | Caller lacks the role needed to perform the operation. | Use an account with the appropriate access role. |
| `404 Not Found` | `COURSE_NOT_FOUND` | No course matched the given code or UUID. | Check `/api/v1/courses` for valid course codes. |
| `404 Not Found` | `TRANSCRIPT_NOT_FOUND` | The item is not a video or does not have a transcript for the requested language. | Check item content type via `/api/v1/items/{item_id}/content`. |
| `422 Unprocessable`| `REQUEST_VALIDATION_FAILED` | Request JSON body missing required fields or incorrect data types. | Inspect the `errors` array in the response envelope for details. |
| `500 Server Error` | `INTERNAL_SERVER_ERROR` | An uncaught server-side exception occurred. | Check server logs with the `X-Correlation-Id` for the stack trace. |

---

## 5. Architectural Rule for Future AI Feature Developers

When implementing the 5 AI features (SchedulAI, Flashcards, Pictorial, Podcast, Slide Deck):
1. **Never make routes call the database or LLMs directly**:
   - HTTP routes must only call application services in `src/app/api/v1/services/`.
2. **Retrieve ground-truth data using existing services**:
   - To build Flashcards or Podcasts, call `content_service.get_item_transcript(session, item_id=...)` rather than writing custom raw SQL.
3. **Always wrap responses in `ApiResponse[T]`**:
   - Maintain the standard envelope for consistency across all frontend clients.
