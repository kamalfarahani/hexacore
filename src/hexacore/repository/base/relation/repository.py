from abc import ABC, abstractmethod

from katharos.types import Result

from hexacore.relation import BaseRelation, BaseRelationMutation
from hexacore.repository.exceptions import UnsupportedMutationError


class BaseRelationRepository[R: BaseRelation](ABC):
    """Define the interface for executing pending relation mutations."""

    @abstractmethod
    def execute_mutations(
        self,
        mutations: list[BaseRelationMutation],
    ) -> Result[UnsupportedMutationError, None]:
        """Execute the pending mutations collected by a relation.

        Args:
            mutations: List of mutations to execute on the relation.

        Returns:
            Success containing None after execution, or failure containing
            an unsupported-mutation error.
        """
        ...
