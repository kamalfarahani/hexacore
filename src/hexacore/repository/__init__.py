from .base import BaseDBCommand, BaseEntityRepository, BaseRelationRepository

type BaseRepository = BaseEntityRepository | BaseRelationRepository

__all__ = [
    "BaseDBCommand",
    "BaseEntityRepository",
    "BaseRelationRepository",
    "BaseRepository",
]
