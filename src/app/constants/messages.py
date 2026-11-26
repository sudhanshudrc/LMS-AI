"""User-facing and error messages for API responses and exceptions."""

from typing import Final

# Generic & System Errors
INTERNAL_SERVER_ERROR: Final = "Something went wrong. Please try again later."
REQUEST_VALIDATION_FAILED: Final = "Request validation failed."
RESOURCE_NOT_FOUND: Final = "The requested resource was not found."
FEATURE_DISABLED: Final = "This feature is currently disabled."
RATE_LIMIT_EXCEEDED: Final = "Too many requests. Please wait a minute and try again."

# Authentication & Authorization Errors
INVALID_CREDENTIALS: Final = "Invalid email or password."
INVALID_SERVICE_TOKEN: Final = "Invalid or expired authentication token."
UNAUTHORIZED_ACCESS: Final = "Authentication credentials were not provided or are invalid."
PERMISSION_DENIED: Final = "You do not have permission to perform this action."
USER_INACTIVE: Final = "User account is inactive."
USER_ALREADY_EXISTS: Final = "A user with this email address already exists."

# Course & Curriculum Domain Errors
COURSE_NOT_FOUND: Final = "The requested course was not found."
MODULE_NOT_FOUND: Final = "The requested module was not found."
SECTION_NOT_FOUND: Final = "The requested section was not found."
SECTION_ITEM_NOT_FOUND: Final = "The requested section item was not found."
CONTENT_NOT_FOUND: Final = "No video or text content found for this item."
TRANSCRIPT_NOT_FOUND: Final = "No transcript is available for this lecture."
PREREQUISITES_NOT_MET: Final = "Course prerequisites have not been satisfied."

# AI & LLM Engine Errors
LLM_TIMEOUT: Final = "The AI service took too long to respond. Please try again."
LLM_PROVIDER_ERROR: Final = (
    "The AI service could not be reached. Check API configuration or try again later."
)
LLM_OUTPUT_INVALID: Final = "The AI model returned an unexpected or malformed response."
LLM_CONTEXT_WINDOW_EXCEEDED: Final = (
    "The course content is too large to process in a single request."
)
LLM_QUOTA_EXCEEDED: Final = "The AI service quota has been exceeded. Please try again later."
EMBEDDING_GENERATION_FAILED: Final = "Failed to generate vector embeddings for the content."

# SchedulAI Feature Errors (F1)
INVALID_DATE_RANGE: Final = "`start_date` must be on or before `end_date`."
DATE_RANGE_TOO_LONG: Final = "The date range must not exceed the allowed limit."
SCHEDULE_CONFLICT: Final = "A schedule already exists for this timeframe."
EMPTY_STUDY_HOURS: Final = "Available study hours must be greater than zero."

# Flashcards Feature Errors (F2)
FLASHCARD_DECK_NOT_FOUND: Final = "Flashcard deck not found."
NO_CONTENT_FOR_FLASHCARDS: Final = (
    "Not enough transcript or text content available to generate flashcards."
)

# Pictorial Feature Errors (F3)
DIAGRAM_GENERATION_FAILED: Final = "Failed to generate visual diagram for this concept."
MISCONCEPTION_ANALYSIS_FAILED: Final = "Unable to analyze learner misconception at this time."

# Podcast Feature Errors (F4)
PODCAST_GENERATION_FAILED: Final = "Failed to generate podcast dialogue."
TTS_SYNTHESIS_FAILED: Final = "Audio voice synthesis failed for the podcast script."
EMPTY_TRANSCRIPT_FOR_PODCAST: Final = "Cannot generate a podcast from an empty transcript."

# Slide Deck Feature Errors (F5)
SLIDEDECK_GENERATION_FAILED: Final = "Failed to generate presentation slides."
SLIDE_PARSE_FAILED: Final = "Failed to parse slide deck structure from generated output."

# Progress Tracking Errors
INVALID_PLAYBACK_POSITION: Final = "Playback position must be a non-negative number."
COMPLETION_ALREADY_RECORDED: Final = "Item completion has already been recorded."
