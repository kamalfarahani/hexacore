from pydantic import BaseModel, ConfigDict


class BaseRelationCommand(BaseModel):
    """Base class for relation commands.

    Subclasses define the fields needed for a specific operation.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
