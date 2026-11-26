"""FastAPI dependency aliases."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session

# Canonical database dependency alias for all FastAPI routes
DbSession = Annotated[AsyncSession, Depends(get_db_session)]

__all__ = ["DbSession"]
