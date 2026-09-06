from pydantic import BaseModel


class BaseRelationCommand(BaseModel):
    """Base class for relation commands.

    Subclasses define the fields needed for a specific operation.
    """
