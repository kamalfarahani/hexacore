from abc import ABC, abstractmethod

from hexacore.relation import BaseRelation


class BaseRelationRepository[R: BaseRelation](ABC):
    """Define the interface for executing pending relation mutations."""

    @abstractmethod
    def execute_mutations(self, relation: R):
        """Execute the pending mutations collected by a relation.

        Args:
            relation: Relation containing the mutations to execute.
        """
        ...
