"""Base event types for hexacore applications."""

from pydantic import BaseModel


class BaseEvent(BaseModel):
    """Base class for all domain events."""
