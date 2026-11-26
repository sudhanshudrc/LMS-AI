"""Integration tests for Phase 3 content delivery and transcript retrieval endpoints."""

import uuid

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import messages
from app.db.models.content import ItemTextContent, ItemVideoContent
from app.db.session import get_db_session
from app.main import app


@pytest.mark.asyncio
async def test_get_video_item_content_and_transcript(db_session: AsyncSession) -> None:
    """Verify GET /api/v1/items/{item_id}/content and /transcript for video items."""
    app.dependency_overrides[get_db_session] = lambda: db_session
    try:
        stmt = select(ItemVideoContent).limit(1)
        video = (await db_session.scalars(stmt)).first()
        assert video is not None
        item_id = video.section_item_id

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as async_client:
            # Test Item Content
            content_resp = await async_client.get(f"/api/v1/items/{item_id}/content")
            assert content_resp.status_code == 200
            content_data = content_resp.json()["data"]
            assert content_data["item_id"] == str(item_id)
            assert content_data["video"] is not None
            assert content_data["video"]["video_url"] == video.video_url
            assert content_data["text"] is None

            # Test Item Transcript
            transcript_resp = await async_client.get(
                f"/api/v1/items/{item_id}/transcript"
            )
            assert transcript_resp.status_code == 200
            t_data = transcript_resp.json()["data"]
            assert t_data["video_content_id"] == str(video.id)
            assert len(t_data["full_text"]) > 0
            assert isinstance(t_data["timed_cues"], list)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_text_item_content(db_session: AsyncSession) -> None:
    """Verify GET /api/v1/items/{item_id}/content for markdown reading items."""
    app.dependency_overrides[get_db_session] = lambda: db_session
    try:
        stmt = select(ItemTextContent).limit(1)
        text_content = (await db_session.scalars(stmt)).first()
        assert text_content is not None
        item_id = text_content.section_item_id

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as async_client:
            content_resp = await async_client.get(f"/api/v1/items/{item_id}/content")
            assert content_resp.status_code == 200
            content_data = content_resp.json()["data"]
            assert content_data["item_id"] == str(item_id)
            assert content_data["video"] is None
            assert content_data["text"] is not None
            assert len(content_data["text"]["body_markdown"]) > 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_item_transcript_not_found(db_session: AsyncSession) -> None:
    """Verify 404 when requesting transcript for a non-existent item."""
    app.dependency_overrides[get_db_session] = lambda: db_session
    try:
        random_id = uuid.uuid4()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as async_client:
            resp = await async_client.get(f"/api/v1/items/{random_id}/transcript")
            assert resp.status_code == 404
            assert resp.json()["message"] == messages.TRANSCRIPT_NOT_FOUND
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_transcripts_fulltext_endpoint(db_session: AsyncSession) -> None:
    """Verify GET /api/v1/transcripts/search returns ranked keyword matches."""
    app.dependency_overrides[get_db_session] = lambda: db_session
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as async_client:
            resp = await async_client.get(
                "/api/v1/transcripts/search?query=programming&limit=5"
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["success"] is True
            assert isinstance(body["data"], list)
            if len(body["data"]) > 0:
                first_result = body["data"][0]
                assert "snippet" in first_result
                assert "rank" in first_result
                assert first_result["rank"] > 0
    finally:
        app.dependency_overrides.clear()
