#!/usr/bin/env python3
"""
LMS Database Setup & Data Ingestion Engine
============================================================================
Performs complete, end-to-end database initialization:
1. Applies PostgreSQL schema DDL (plan/schema.sql)
2. Parses raw course data from data/LMSxAI.xlsx
3. Parses timestamped transcripts from data/Transcript_data/*.txt
4. Synthesizes Markdown study guides from study materials & video summaries
5. Seeds courses, prerequisites, modules, sections, videos, transcripts & notes
============================================================================
Can be executed in two ways:
  - Directly via Python: ./scripts/init_and_seed.py
  - Or via Docker CLI:   python3 scripts/init_and_seed.py --docker
"""

import os
import re
import sys
import json
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXCEL_PATH = os.path.join(DATA_DIR, "LMSxAI.xlsx")
TRANSCRIPT_DIR = os.path.join(DATA_DIR, "Transcript_data")
SCHEMA_SQL_PATH = os.path.join(BASE_DIR, "plan", "schema.sql")

DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
DB_NAME = os.environ.get("POSTGRES_DB", "lms_db")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres_secure_password")
DOCKER_CONTAINER = os.environ.get("DOCKER_CONTAINER", "lms_postgres")

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
    """Parse LMSxAI.xlsx without external libraries."""
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
    if not url:
        return None
    match = re.search(r'(?:youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]{11})', url)
    return match.group(1) if match else None


def parse_transcript_file(file_path: str):
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

    return timed_cues, full_text, "\n".join(vtt_lines)


def generate_study_guide_markdown(lecture: Dict[str, Any]) -> str:
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


def build_full_migration_sql(lectures: List[Dict[str, Any]]) -> str:
    """Build unified SQL script containing Schema DDL + Enriched Seed Data."""
    with open(SCHEMA_SQL_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    sql_statements = [
        "-- ============================================================================",
        "-- 1. DATABASE SCHEMA CREATION (Idempotent DDL)",
        "-- ============================================================================",
        schema_sql,
        "",
        "-- ============================================================================",
        "-- 2. SEED DATA ENRICHMENT",
        "-- ============================================================================",
        "BEGIN;",
        "",
        "-- Default Users",
        "INSERT INTO users (email, password_hash, full_name, role)",
        "VALUES",
        "    ('admin@lms.local', '$2b$12$K8y6zQ8w9x.sample_admin_hash_placeholder', 'LMS Administrator', 'admin'),",
        "    ('student@lms.local', '$2b$12$K8y6zQ8w9x.sample_student_hash_placeholder', 'Alex Learner', 'user')",
        "ON CONFLICT (email) DO NOTHING;",
        ""
    ]

    from collections import defaultdict
    course_groups = defaultdict(list)
    for lec in lectures:
        raw_c = lec["raw_course"] or "C++"
        course_groups[raw_c].append(lec)

    # Courses
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

    # Prerequisites
    for target_code, prereq_codes in PREREQUISITES_MAP.items():
        for p_code in prereq_codes:
            sql_statements.append(f"""
INSERT INTO course_prerequisites (course_id, prerequisite_course_id)
SELECT c1.id, c2.id FROM courses c1, courses c2
WHERE c1.course_id = '{target_code}' AND c2.course_id = '{p_code}'
ON CONFLICT (course_id, prerequisite_course_id) DO NOTHING;""")

    # Modules, Sections, Items
    for raw_c, lecs in course_groups.items():
        cat_meta = COURSE_CATALOG.get(raw_c)
        if not cat_meta:
            continue
        c_code = cat_meta["course_id"]
        mod_title = f"Core Module: {cat_meta['title']}".replace("'", "''")
        mod_desc = f"Essential learning sequence for {raw_c}".replace("'", "''")

        sql_statements.append(f"""
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

            # Video item
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

            # Text item
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
    return "\n".join(sql_statements)


def execute_via_docker(sql_content: str):
    """Execute SQL directly into the running Docker container via docker exec."""
    print(f"Connecting to container '{DOCKER_CONTAINER}' via docker exec...")
    cmd = ["docker", "exec", "-i", DOCKER_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate(input=sql_content)
    if proc.returncode != 0:
        print(f"Error executing SQL in container: {err}", file=sys.stderr)
        sys.exit(1)
    print("Database schema creation and data seeding completed successfully.")


def main():
    print("=================================================================")
    print("LMS Database Initialization & Data Seeding Engine")
    print("=================================================================")
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: Excel file not found at {EXCEL_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading data from: {DATA_DIR}")
    lectures = read_excel_sheet2(EXCEL_PATH)
    print(f"Loaded {len(lectures)} lectures across 5 course categories.")

    print("Building unified migration and seed SQL...")
    full_sql = build_full_migration_sql(lectures)
    
    # Save a reproducible copy in scripts/seed_data.sql
    out_sql = os.path.join(BASE_DIR, "scripts", "seed_data.sql")
    with open(out_sql, "w", encoding="utf-8") as f:
        f.write(full_sql)
    print(f"Generated unified SQL script: {out_sql} ({len(full_sql)} bytes)")

    # Execute into database
    execute_via_docker(full_sql)
    print("=================================================================")
    print("Your PostgreSQL database is fully initialized and enriched.")
    print("=================================================================")


if __name__ == "__main__":
    main()
