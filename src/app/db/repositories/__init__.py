"""Repositories package."""

from app.db.repositories.content_repository import (
    get_text_content_by_item,
    get_transcript_by_language,
    get_video_content_by_item,
    search_transcripts_fulltext,
)
from app.db.repositories.course_repository import (
    find_course_by_code,
    find_course_by_id,
    list_course_prerequisites,
    list_published_courses,
)
from app.db.repositories.curriculum_repository import (
    find_module_by_id,
    find_section_by_id,
    get_course_tree,
    list_section_items,
)
from app.db.repositories.progress_repository import (
    get_user_item_completion,
    get_user_module_completion,
    save_playback_position,
    upsert_user_module_completion,
)
from app.db.repositories.user_repository import (
    create_user,
    find_user_by_email,
    find_user_by_id,
    list_users,
)

__all__ = [
    "create_user",
    "find_course_by_code",
    "find_course_by_id",
    "find_module_by_id",
    "find_section_by_id",
    "find_user_by_email",
    "find_user_by_id",
    "get_course_tree",
    "get_text_content_by_item",
    "get_transcript_by_language",
    "get_user_item_completion",
    "get_user_module_completion",
    "get_video_content_by_item",
    "list_course_prerequisites",
    "list_published_courses",
    "list_section_items",
    "list_users",
    "save_playback_position",
    "search_transcripts_fulltext",
    "upsert_user_module_completion",
]
