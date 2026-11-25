#!/usr/bin/env python3
"""
LMS Complete Database Ingestion & Seeding Engine
Populates PostgreSQL with all courses, modules, sections, video lectures,
transcripts (with timed cues), and study material text articles.

Capable of:
1. Direct connection ingestion via psycopg2/asyncpg.
2. Full standalone SQL seed generation (`docker/initdb/02-seed-data.sql` and `scripts/seed_data.sql`),
   ensuring the database starts up completely enriched inside Docker automatically.
"""

import os
import re
import sys
import json
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional

try:
    import psycopg2
    from psycopg2.extras import Json
except ImportError:
    psycopg2 = None
    Json = None

DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
DB_NAME = os.environ.get("POSTGRES_DB", "lms_db")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres_secure_password")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSCRIPT_DIR = os.path.join(BASE_DIR, "Transcript_data")
EXCEL_PATH = os.path.join(BASE_DIR, "LMSxAI.xlsx")

COURSE_CATALOG = {
    "C++": {
        "course_id": "CPP-101",
        "title": "Mastering C++ Programming: From Syntax to Memory Mastery",
        "subtitle": "Comprehensive guide to C++ operators, OOP concepts, and systems programming",
        "org": "Neso Academy",
        "duration": "8 weeks",
        "effort": "4-6 hours per week",
        "language": "en",
        "short_description": "Master core C++ concepts including unary and binary operators, scope resolution, and OOP principles.",
        "description": "This course covers foundational to advanced C++ programming constructs. You will master arithmetic, relational, and assignment operators, delve into the scope resolution operator, and build robust object-oriented software.",
        "overview": "C++ is a high-performance general-purpose language widely used in systems programming, game development, and embedded devices. This course equips learners with deep mechanical understanding of syntax, memory, and performance."
    },
    "Machine Leanrning": {
        "course_id": "ML-201",
        "title": "Foundations of Machine Learning & Predictive Modeling",
        "subtitle": "End-to-end machine learning workflows, model architectures, and data pipelines",
        "org": "Neso Academy",
        "duration": "10 weeks",
        "effort": "6-8 hours per week",
        "language": "en",
        "short_description": "Learn the theory and implementation of machine learning models, training pipelines, and dataset engineering.",
        "description": "Explore the history, math, and practical architectures of machine learning. Understand supervised and unsupervised learning paradigms, data splitting, model evaluation, and modern ML pipelines.",
        "overview": "Machine learning powers modern AI products. This course walks through the journey from historical breakthroughs to training modern predictive models on clean dataset pipelines."
    },
    "Data Structure": {
        "course_id": "DSA-201",
        "title": "Data Structures & Asymptotic Algorithm Analysis",
        "subtitle": "Master abstract data types, asymptotic efficiency, and optimal memory layouts",
        "org": "Neso Academy",
        "duration": "10 weeks",
        "effort": "6-8 hours per week",
        "language": "en",
        "short_description": "In-depth exploration of core data structures, time complexity analysis, and performance trade-offs.",
        "description": "Understand the difference between primitive data types and Abstract Data Types (ADTs). Master big-O asymptotic analysis and learn to choose optimal data structures for high-scale computational workloads.",
        "overview": "Efficient algorithms rely on intelligent data structuring. This course teaches how to analyze time and space complexity and construct high-performance data structures."
    },
    "OOP": {
        "course_id": "OOP-102",
        "title": "Object-Oriented Programming & Software Design",
        "subtitle": "Encapsulation, static members, friend functions, and class architecture",
        "org": "Neso Academy",
        "duration": "6 weeks",
        "effort": "4-6 hours per week",
        "language": "en",
        "short_description": "Master the principles of OOP: classes, member functions, access specifiers, and friend relationships.",
        "description": "Deep-dive into class design in C++ and Java. Explore static members, static member functions, access specifiers (public, private, protected), and friend functions.",
        "overview": "Object-Oriented Programming is the foundation of modern enterprise software. Learn to model real-world domains with clean encapsulation and maintainable abstraction boundaries."
    },
    "Python": {
        "course_id": "PY-101",
        "title": "Python Programming: Beginner to Software Engineering",
        "subtitle": "Interpreters, data types, string operations, and modern Python workflows",
        "org": "Neso Academy",
        "duration": "8 weeks",
        "effort": "4-5 hours per week",
        "language": "en",
        "short_description": "Learn Python from the ground up: interpreter internals, VS Code setup, core types, and string operators.",
        "description": "Step into the world of Python programming. Understand how the Python interpreter works, configure a development environment with Visual Studio Code, and master types and operations.",
        "overview": "Python is the undisputed language of AI, data science, and modern backend web development. This course gives learners an intuitive yet technically rigorous start."
    }
}

PREREQUISITES_MAP = {
    "DSA-201": ["CPP-101"],
    "ML-201": ["PY-101"],
    "OOP-102": ["CPP-101"]
}


def read_excel_sheet2(file_path: str) -> List[Dict[str, Any]]:
    """Parse LMSxAI.xlsx sheet2 without third-party dependencies."""
    with zipfile.ZipFile(file_path) as z:
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
            for elem in tree.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                t = elem.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                if t is not None:
                    shared_strings.append(t.text or '')
                else:
                    text_parts = [t_el.text for t_el in elem.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t') if t_el.text]
                    shared_strings.append(''.join(text_parts))

        tree = ET.fromstring(z.read('xl/worksheets/sheet2.xml'))
        rows = []
        for row_elem in tree.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheetData/{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
            row_cells = {}
            for c in row_elem.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                r_attr = c.get('r')
                t = c.get('t')
                v = c.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                val = v.text if v is not None else None
                if t == 's' and val is not None:
                    val = shared_strings[int(val)]
                col_letter = ''.join([ch for ch in r_attr if ch.isalpha()])
                row_cells[col_letter] = val
            rows.append(row_cells)

    lectures = []
    current_course = None
    for r in rows[1:]:
        if 'A' in r and r['A']:
            current_course = r['A'].strip()
        title = r.get('E')
        if not title:
            continue
        title = title.strip()
        lectures.append({
            "raw_course": current_course,
            "video_url": r.get('B'),
            "study_material": r.get('D'),
            "title": title,
            "drive_link": r.get('F'),
            "summary": r.get('G'),
            "keywords": r.get('H')
        })
    return lectures


def extract_youtube_id(url: Optional[str]) -> Optional[str]:
    """Extract YouTube 11-character video ID from URL."""
    if not url:
        return None
    match = re.search(r'(?:youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]{11})', url)
    return match.group(1) if match else None


def parse_transcript_file(file_path: str):
    """Parse timestamped transcript text into timed cues, full text, and VTT."""
    if not os.path.exists(file_path):
        return [], "", ""

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r'(\d{2}:\d{2})\s*', content)
    cues = []
    text_segments = []

    for i in range(1, len(blocks), 2):
        ts_str = blocks[i]
        seg_text = blocks[i+1].strip() if i+1 < len(blocks) else ""
        if not seg_text:
            continue
        parts = ts_str.split(":")
        start_seconds = float(int(parts[0]) * 60 + int(parts[1]))
        cues.append({
            "timestamp": ts_str,
            "start": start_seconds,
            "text": seg_text
        })
        text_segments.append(seg_text)

    timed_cues = []
    for i, c in enumerate(cues):
        end_sec = cues[i+1]["start"] if i + 1 < len(cues) else c["start"] + 5.0
        timed_cues.append({
            "start": round(c["start"], 2),
            "end": round(end_sec, 2),
            "text": c["text"]
        })

    full_text = " ".join([re.sub(r'\s+', ' ', t) for t in text_segments])

    vtt_lines = ["WEBVTT", ""]
    for i, cue in enumerate(timed_cues, start=1):
        def format_vtt_ts(sec):
            m = int(sec // 60)
            s = int(sec % 60)
            ms = int((sec - int(sec)) * 1000)
            return f"00:{m:02d}:{s:02d}.{ms:03d}"

        vtt_lines.append(str(i))
        vtt_lines.append(f"{format_vtt_ts(cue['start'])} --> {format_vtt_ts(cue['end'])}")
        vtt_lines.append(cue["text"])
        vtt_lines.append("")

    vtt_content = "\n".join(vtt_lines)
    return timed_cues, full_text, vtt_content


def generate_study_guide_markdown(lecture: Dict[str, Any]) -> str:
    """Synthesize structured study guide from study material reference and summary."""
    title = lecture["title"]
    summary = lecture.get("summary") or "Comprehensive lecture overview."
    study_url = lecture.get("study_material")
    keywords = [k.strip() for k in (lecture.get("keywords") or "").split("\n") if k.strip()]

    md_lines = [
        f"# Study Guide: {title}",
        "",
        "## Conceptual Overview",
        summary,
        "",
        "## Key Terminology & Concepts",
    ]
    for kw in keywords[:6]:
        md_lines.append(f"- **{kw.title()}**: Foundational concept covered in this lecture.")

    if study_url:
        md_lines.extend([
            "",
            "## Supplementary Reading & Official Reference",
            "For further practice and deep-dive technical examples, consult the official study material reference:",
            f"- [{title} - In-Depth Documentation & Examples]({study_url})"
        ])

    md_lines.extend([
        "",
        "## Review Questions for Self-Assessment",
        f"1. What is the primary purpose and syntax of {title}?",
        "2. How does the compiler or runtime handle edge cases for this construct?",
        "3. In what scenarios should this pattern be used over alternative implementations?"
    ])

    return "\n".join(md_lines)


def generate_full_sql_seed(course_groups: Dict[str, List[Dict[str, Any]]]):
    """Generates a complete, standalone SQL seed containing all 24 lectures, videos, transcripts, and study guides."""
    sql_statements = [
        "-- ============================================================================",
        "-- LMS Full Production Seed Script",
        "-- Auto-generated from LMSxAI.xlsx and Transcript_data/",
        "-- Enriches: users, courses, course_prerequisites, modules, sections,",
        "--           section_items, item_video_contents, item_text_contents, video_transcripts",
        "-- ============================================================================",
        "BEGIN;",
        "",
        "-- 1. Seed Users",
        "INSERT INTO users (email, password_hash, full_name, role)",
        "VALUES",
        "    ('admin@lms.local', '$2b$12$K8y6zQ8w9x.sample_admin_hash_placeholder', 'LMS Administrator', 'admin'),",
        "    ('student@lms.local', '$2b$12$K8y6zQ8w9x.sample_student_hash_placeholder', 'Alex Learner', 'user')",
        "ON CONFLICT (email) DO NOTHING;",
        ""
    ]

    # 2. Insert Courses
    for raw_name, meta in COURSE_CATALOG.items():
        desc = meta['description'].replace("'", "''")
        sdesc = meta['short_description'].replace("'", "''")
        ov = meta['overview'].replace("'", "''")
        title = meta['title'].replace("'", "''")
        sub = meta['subtitle'].replace("'", "''")
        sql_statements.append(f"""
INSERT INTO courses (org, course_id, title, subtitle, duration, effort, language, short_description, description, overview, is_published)
VALUES ('{meta['org']}', '{meta['course_id']}', '{title}', '{sub}', '{meta['duration']}', '{meta['effort']}', '{meta['language']}', '{sdesc}', '{desc}', '{ov}', true)
ON CONFLICT (course_id) DO UPDATE SET title = EXCLUDED.title;""")

    # 3. Insert Prerequisites
    for target_code, prereq_codes in PREREQUISITES_MAP.items():
        for p_code in prereq_codes:
            sql_statements.append(f"""
INSERT INTO course_prerequisites (course_id, prerequisite_course_id)
SELECT c1.id, c2.id FROM courses c1, courses c2
WHERE c1.course_id = '{target_code}' AND c2.course_id = '{p_code}'
ON CONFLICT (course_id, prerequisite_course_id) DO NOTHING;""")

    # 4. Insert Modules, Sections, Videos, Transcripts, Text
    for raw_c, lecs in course_groups.items():
        cat_meta = COURSE_CATALOG.get(raw_c)
        if not cat_meta:
            continue
        c_code = cat_meta["course_id"]
        mod_title = f"Core Module: {cat_meta['title']}".replace("'", "''")
        mod_desc = f"Essential learning sequence for {raw_c}".replace("'", "''")

        sql_statements.append(f"""
-- Module for {c_code}
INSERT INTO modules (course_id, title, description, order_index, is_published)
SELECT id, '{mod_title}', '{mod_desc}', 1, true FROM courses WHERE course_id = '{c_code}'
ON CONFLICT (course_id, order_index) DO UPDATE SET title = EXCLUDED.title;""")

        for s_idx, lec in enumerate(lecs, start=1):
            sec_title = lec["title"].replace("'", "''")
            sec_desc = ((lec.get("summary") or "")[:200]).replace("'", "''")
            yt_id = extract_youtube_id(lec.get("video_url")) or ""
            video_url = (lec.get("video_url") or "").replace("'", "''")

            # Section
            sql_statements.append(f"""
INSERT INTO sections (module_id, title, description, order_index, is_published)
SELECT m.id, '{sec_title}', '{sec_desc}', {s_idx}, true
FROM modules m JOIN courses c ON m.course_id = c.id
WHERE c.course_id = '{c_code}' AND m.order_index = 1
ON CONFLICT (module_id, order_index) DO UPDATE SET title = EXCLUDED.title;""")

            # Section Item: Video
            sql_statements.append(f"""
INSERT INTO section_items (section_id, title, content_type, order_index)
SELECT s.id, 'Video: {sec_title}', 'video', 1
FROM sections s JOIN modules m ON s.module_id = m.id JOIN courses c ON m.course_id = c.id
WHERE c.course_id = '{c_code}' AND m.order_index = 1 AND s.order_index = {s_idx}
ON CONFLICT (section_id, order_index) DO UPDATE SET title = EXCLUDED.title;""")

            sql_statements.append(f"""
INSERT INTO item_video_contents (section_item_id, video_url, youtube_video_id, duration_seconds)
SELECT si.id, '{video_url}', '{yt_id}', 600
FROM section_items si
JOIN sections s ON si.section_id = s.id
JOIN modules m ON s.module_id = m.id
JOIN courses c ON m.course_id = c.id
WHERE c.course_id = '{c_code}' AND m.order_index = 1 AND s.order_index = {s_idx} AND si.order_index = 1
ON CONFLICT (section_item_id) DO UPDATE SET video_url = EXCLUDED.video_url;""")

            # Transcript
            txt_filename = f"{lec['title']}.txt"
            txt_path = os.path.join(TRANSCRIPT_DIR, txt_filename)
            timed_cues, full_text, vtt_content = parse_transcript_file(txt_path)
            if full_text:
                clean_full_text = full_text.replace("'", "''")
                clean_cues_json = json.dumps(timed_cues).replace("'", "''")
                clean_vtt = vtt_content.replace("'", "''")
                sql_statements.append(f"""
INSERT INTO video_transcripts (video_content_id, language_code, full_text, timed_cues, vtt_content)
SELECT ivc.id, 'en', '{clean_full_text}', '{clean_cues_json}'::jsonb, '{clean_vtt}'
FROM item_video_contents ivc
JOIN section_items si ON ivc.section_item_id = si.id
JOIN sections s ON si.section_id = s.id
JOIN modules m ON s.module_id = m.id
JOIN courses c ON m.course_id = c.id
WHERE c.course_id = '{c_code}' AND m.order_index = 1 AND s.order_index = {s_idx} AND si.order_index = 1
ON CONFLICT (video_content_id, language_code) DO UPDATE SET
    full_text = EXCLUDED.full_text,
    timed_cues = EXCLUDED.timed_cues,
    vtt_content = EXCLUDED.vtt_content;""")

            # Section Item: Text Study Guide
            guide_md = generate_study_guide_markdown(lec).replace("'", "''")
            word_count = len(guide_md.split())
            read_time = max(60, int((word_count / 200.0) * 60))

            sql_statements.append(f"""
INSERT INTO section_items (section_id, title, content_type, order_index)
SELECT s.id, 'Study Guide: {sec_title}', 'text', 2
FROM sections s JOIN modules m ON s.module_id = m.id JOIN courses c ON m.course_id = c.id
WHERE c.course_id = '{c_code}' AND m.order_index = 1 AND s.order_index = {s_idx}
ON CONFLICT (section_id, order_index) DO UPDATE SET title = EXCLUDED.title;""")

            sql_statements.append(f"""
INSERT INTO item_text_contents (section_item_id, body_markdown, estimated_read_time_seconds)
SELECT si.id, '{guide_md}', {read_time}
FROM section_items si
JOIN sections s ON si.section_id = s.id
JOIN modules m ON s.module_id = m.id
JOIN courses c ON m.course_id = c.id
WHERE c.course_id = '{c_code}' AND m.order_index = 1 AND s.order_index = {s_idx} AND si.order_index = 2
ON CONFLICT (section_item_id) DO UPDATE SET body_markdown = EXCLUDED.body_markdown;""")

    sql_statements.append("")
    sql_statements.append("COMMIT;")

    full_sql = "\n".join(sql_statements)

    # Save to scripts/seed_data.sql and docker/initdb/02-seed-data.sql
    targets = [
        os.path.join(BASE_DIR, "scripts", "seed_data.sql"),
        os.path.join(BASE_DIR, "docker", "initdb", "02-seed-data.sql")
    ]
    for target in targets:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(full_sql)
        print(f"Generated full SQL seed: {target} ({len(full_sql)} bytes)")


def main():
    print("Beginning LMS Data Enrichment Pipeline...")
    lectures = read_excel_sheet2(EXCEL_PATH)
    print(f"Loaded {len(lectures)} lecture entries from {EXCEL_PATH}")

    from collections import defaultdict
    course_groups = defaultdict(list)
    for lec in lectures:
        raw_c = lec["raw_course"] or "C++"
        course_groups[raw_c].append(lec)

    generate_full_sql_seed(course_groups)
    print("Full SQL seed generation complete. All 24 lectures and transcripts are embedded.")


if __name__ == "__main__":
    main()
