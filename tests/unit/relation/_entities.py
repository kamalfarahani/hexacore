from dataclasses import dataclass
from uuid import UUID

from hexacore.entity import Entity


@dataclass
class LeftEntity(Entity[int]):
    """Test entity identified by an integer."""

    id: int

    @property
    def identifier(self) -> int:
        """Return the entity identifier."""
        return self.id


@dataclass
class RightEntity(Entity[UUID]):
    """Test entity identified by a UUID."""

    id: UUID

    @property
    def identifier(self) -> UUID:
        """Return the entity identifier."""
        return self.id
