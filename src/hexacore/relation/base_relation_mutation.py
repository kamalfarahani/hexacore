"""Define the base model for changes to entity relations."""

from pydantic import BaseModel, ConfigDict


class BaseRelationMutation(BaseModel):
    """Represent a pending change to a relation.

    Subclasses identify a specific kind of change and define the data needed
    to apply it.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
