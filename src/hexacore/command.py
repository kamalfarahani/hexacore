"""Base command types for hexacore applications."""

from pydantic import BaseModel


class BaseCommand(BaseModel):
    """Base class for all domain commands."""
