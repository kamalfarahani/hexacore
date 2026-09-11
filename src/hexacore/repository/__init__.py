from .base import BaseDBCommand, BaseEntityRepository, BaseRelationRepository
from .sqlalchemy import SQLAlchemyEntityRepository, SQLAlchemyRelationRepository

type BaseRepository = BaseEntityRepository | BaseRelationRepository

__all__ = [
    "BaseDBCommand",
    "BaseEntityRepository",
    "BaseRelationRepository",
    "BaseRepository",
    "SQLAlchemyEntityRepository",
    "SQLAlchemyRelationRepository",
]
