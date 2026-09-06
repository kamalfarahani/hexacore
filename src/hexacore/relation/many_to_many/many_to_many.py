"""Collect mutations representing changes to many-to-many relations."""

from hexacore.entity import Entity

from ..base_relation import BaseRelation
from .mutations import Create, Unlink, UpdateLeft, UpdateRight


class ManyToMany[L_ID, R_ID, L: Entity, R: Entity](BaseRelation):
    """Collect changes to a relation between many left and many right entities.

    Methods record mutations for later processing. They do not apply the
    represented changes or enforce cardinality.
    """

    def create(self, left_id: L_ID, right_id: R_ID) -> None:
        """Record a mutation that links one left entity to one right entity.

        Args:
            left_id: Identifier of the left entity to link.
            right_id: Identifier of the right entity to link.
        """
        self.add_mutation(Create[L_ID, R_ID](left_id=left_id, right_id=right_id))

    def update_left(self, right_id: R_ID, left: L) -> None:
        """Record a mutation that changes one left entity in the relation.

        Args:
            right_id: Identifier of the right entity associated with the left entity.
            left: Entity supplied for the update, with its identifier selecting
                the left entity within the relation.
        """
        self.add_mutation(UpdateLeft[R_ID, L](right_id=right_id, left=left))

    def update_right(self, left_id: L_ID, right: R) -> None:
        """Record a mutation that changes one right entity in the relation.

        Args:
            left_id: Identifier of the left entity associated with the right entity.
            right: Entity supplied for the update, with its identifier selecting
                the right entity within the relation.
        """
        self.add_mutation(UpdateRight[L_ID, R](left_id=left_id, right=right))

    def unlink(self, left_id: L_ID, right_id: R_ID) -> None:
        """Record a mutation that removes one link between the specified entities.

        Args:
            left_id: Identifier of the left entity to unlink.
            right_id: Identifier of the right entity to unlink.
        """
        self.add_mutation(Unlink[L_ID, R_ID](left_id=left_id, right_id=right_id))
