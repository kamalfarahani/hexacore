from .entity import (
    BaseDBCommand,
    BaseEntityRepository,
)
from .relation import BaseRelationRepository

type BaseRepository = BaseEntityRepository | BaseRelationRepository

__all__ = [
    "BaseDBCommand",
    "BaseEntityRepository",
    "BaseRelationRepository",
    "BaseRepository",
]
