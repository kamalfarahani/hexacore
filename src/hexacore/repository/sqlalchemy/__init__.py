"""Provide subclassable SQLAlchemy repository adapters."""

from .entity import SQLAlchemyEntityRepository
from .relation import SQLAlchemyRelationRepository

__all__ = ["SQLAlchemyEntityRepository", "SQLAlchemyRelationRepository"]
