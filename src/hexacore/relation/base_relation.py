"""Define the base collector for relation mutations."""

from abc import ABC, abstractmethod

from katharos.types import ImmutableList

from .base_relation_mutation import BaseRelationMutation


class BaseRelation(ABC):
    """Collect mutations representing changes to relations between entities."""

    @abstractmethod
    def supported_mutations(self) -> ImmutableList[type[BaseRelationMutation]]: ...
