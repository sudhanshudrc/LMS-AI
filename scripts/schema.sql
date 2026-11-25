-- ============================================================================
-- LMS Database Schema (PostgreSQL 15+)
-- Perspective: Curated Course Catalog with Strict Normalization
-- Built with: .agents/skills/database-design & postgres-best-practices
-- ============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- ENUMS
-- ============================================================================

CREATE TYPE user_role AS ENUM (
    'user',
    'admin'
);

CREATE TYPE content_component_type AS ENUM (
    'text',
    'video'
);

CREATE TYPE completion_status AS ENUM (
    'not_started',
    'in_progress',
    'completed'
);

-- ============================================================================
-- 1. USERS & AUTH
-- Simple user model: 'user' or 'admin'. No multi-tier instructor overhead.
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    role user_role NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================================
-- 2. COURSES (Self-Curated)
-- Retains core catalog fields: org, course_id, title, subtitle, start_date,
-- end_date, duration, effort, language, short_description, description, overview.
-- ============================================================================

CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identification & Organization
    org VARCHAR(100) NOT NULL DEFAULT 'Self', -- Organization tag (e.g., 'edX', 'MITx')
    course_id VARCHAR(100) NOT NULL UNIQUE,   -- Canonical course key (e.g., 'CS50x')
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(500) NULL,
    
    -- Schedule & Commitment
    start_date TIMESTAMPTZ NULL,
    end_date TIMESTAMPTZ NULL,
    duration VARCHAR(100) NULL,               -- e.g., '10 weeks', 'Self-paced'
    effort VARCHAR(100) NULL,                 -- e.g., '6-8 hours per week'
    
    -- Language & Descriptions
    language VARCHAR(50) NOT NULL DEFAULT 'en',
    short_description VARCHAR(1000) NULL,
    description TEXT NULL,
    overview TEXT NULL,
    
    is_published BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_courses_course_id ON courses(course_id);
CREATE INDEX idx_courses_org ON courses(org);

-- ============================================================================
-- 2a. COURSE PREREQUISITES (Normalized Self-Referential Junction Table)
-- Avoids unconstrained text arrays. Enforces referential integrity between courses.
-- Self-referencing constraint prevents a course from requiring itself.
-- ============================================================================

CREATE TABLE course_prerequisites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    prerequisite_course_id UUID NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_course_prerequisite UNIQUE (course_id, prerequisite_course_id),
    CONSTRAINT chk_no_self_prerequisite CHECK (course_id <> prerequisite_course_id)
);

CREATE INDEX idx_course_prereq_course ON course_prerequisites(course_id);
CREATE INDEX idx_course_prereq_target ON course_prerequisites(prerequisite_course_id);

-- ============================================================================
-- 3. MODULES (edX Section / Chapter)
-- High-level thematic modules within a course.
-- ============================================================================

CREATE TABLE modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    order_index INTEGER NOT NULL CHECK (order_index >= 0),
    is_published BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_course_module_order UNIQUE (course_id, order_index)
);

CREATE INDEX idx_modules_course_order ON modules(course_id, order_index);

-- ============================================================================
-- 4. SECTIONS (edX Subsection / Sequential)
-- Sub-topics within a module grouping specific content items.
-- ============================================================================

CREATE TABLE sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    order_index INTEGER NOT NULL CHECK (order_index >= 0),
    is_published BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_module_section_order UNIQUE (module_id, order_index)
);

CREATE INDEX idx_sections_module_order ON sections(module_id, order_index);

-- ============================================================================
-- 5. SECTION ITEMS (Ordered units inside sections: Text or Video)
-- ============================================================================

CREATE TABLE section_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content_type content_component_type NOT NULL,
    order_index INTEGER NOT NULL CHECK (order_index >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_section_item_order UNIQUE (section_id, order_index)
);

CREATE INDEX idx_section_items_section_order ON section_items(section_id, order_index);

-- 5a. Text Component
CREATE TABLE item_text_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_item_id UUID NOT NULL UNIQUE REFERENCES section_items(id) ON DELETE CASCADE,
    body_markdown TEXT NOT NULL,
    estimated_read_time_seconds INTEGER NOT NULL DEFAULT 180 CHECK (estimated_read_time_seconds >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5b. YouTube Video Component
CREATE TABLE item_video_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_item_id UUID NOT NULL UNIQUE REFERENCES section_items(id) ON DELETE CASCADE,
    video_url VARCHAR(1000) NOT NULL,
    youtube_video_id VARCHAR(64) NULL, -- Extracted YouTube 11-char ID
    duration_seconds INTEGER NOT NULL DEFAULT 0 CHECK (duration_seconds >= 0),
    thumbnail_url VARCHAR(1000) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_item_video_youtube_id ON item_video_contents(youtube_video_id);

-- 5c. Video Transcripts (Timed subtitles & full text for AI RAG / Interactive Chat)
CREATE TABLE video_transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_content_id UUID NOT NULL REFERENCES item_video_contents(id) ON DELETE CASCADE,
    language_code VARCHAR(10) NOT NULL DEFAULT 'en',
    full_text TEXT NOT NULL,                         -- Continuous plain text for AI retrieval
    timed_cues JSONB NOT NULL DEFAULT '[]'::jsonb,   -- Array of {start: float, end: float, text: string}
    vtt_content TEXT NULL,                           -- Standard WebVTT string
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_video_language UNIQUE (video_content_id, language_code)
);

CREATE INDEX idx_transcripts_video_lang ON video_transcripts(video_content_id, language_code);
-- Full-text search index for AI text discovery across all lectures
CREATE INDEX idx_transcripts_fulltext ON video_transcripts USING gin(to_tsvector('english', full_text));

-- ============================================================================
-- 6. USER PROGRESS & COMPLETION TRACKING
-- Module-level completion recorded user-wise, plus granular item resume state.
-- (No enrollment barriers; any authenticated user can progress through courses).
-- ============================================================================

-- User-wise Module Completion
CREATE TABLE user_module_completions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    status completion_status NOT NULL DEFAULT 'not_started',
    progress_percentage NUMERIC(5, 2) NOT NULL DEFAULT 0.00 CHECK (progress_percentage >= 0.00 AND progress_percentage <= 100.00),
    completed_at TIMESTAMPTZ NULL,
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_module UNIQUE (user_id, module_id)
);

CREATE INDEX idx_user_module_lookup ON user_module_completions(user_id, module_id);
CREATE INDEX idx_user_module_status ON user_module_completions(user_id, status);

-- User-wise Item Completion (Detailed resume position for YouTube video and read status)
CREATE TABLE user_item_completions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    section_item_id UUID NOT NULL REFERENCES section_items(id) ON DELETE CASCADE,
    status completion_status NOT NULL DEFAULT 'not_started',
    last_playback_position_seconds INTEGER NOT NULL DEFAULT 0,
    is_completed BOOLEAN GENERATED ALWAYS AS (status = 'completed') STORED,
    completed_at TIMESTAMPTZ NULL,
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_section_item UNIQUE (user_id, section_item_id)
);

CREATE INDEX idx_user_item_comp_lookup ON user_item_completions(user_id, section_item_id);
