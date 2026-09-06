"""Collect commands for operations on one-to-many relations."""

from hexacore.entity import Entity

from ..base_relation import BaseRelation
from .commands import Create, GetLeft, GetRights, Unlink, UpdateLeft, UpdateRight


class OneToMany[L_ID, R_ID, L: Entity, R: Entity](BaseRelation):
    """Represent a relation from one left entity to many right entities.

    Methods append commands for later processing. They do not execute the
    operations, enforce cardinality, or return retrieved entities.
    """

    def create(self, left_id: L_ID, right_id: R_ID) -> None:
        """Append a command to link one right entity to a left entity.

        Args:
            left_id: Identifier of the left entity to link.
            right_id: Identifier of the right entity to link.
        """
        self.add_command(Create[L_ID, R_ID](left_id=left_id, right_id=right_id))

    def get_left(self, right_id: R_ID) -> None:
        """Append a command to retrieve the left entity linked to a right entity.

        Args:
            right_id: Identifier of the right entity used to locate the left entity.
        """
        self.add_command(GetLeft[R_ID](right_id=right_id))

    def get_rights(self, left_id: L_ID) -> None:
        """Append a command to retrieve all right entities linked to a left entity.

        Args:
            left_id: Identifier of the left entity whose right entities are requested.
        """
        self.add_command(GetRights[L_ID](left_id=left_id))

    def update_left(self, right_id: R_ID, left: L) -> None:
        """Append a command to update the left entity linked to a right entity.

        Args:
            right_id: Identifier of the right entity used to locate the left entity.
            left: Entity supplied for the left-side update.
        """
        self.add_command(UpdateLeft[R_ID, L](right_id=right_id, left=left))

    def update_right(self, left_id: L_ID, right: R) -> None:
        """Append a command to update one right entity linked to a left entity.

        Args:
            left_id: Identifier of the left entity associated with the right entity.
            right: Entity supplied for the update, with its identifier selecting
                the right entity within the relation.
        """
        self.add_command(UpdateRight[L_ID, R](left_id=left_id, right=right))

    def unlink(self, left_id: L_ID, right_id: R_ID) -> None:
        """Append a command to remove one link between the specified entities.

        Args:
            left_id: Identifier of the left entity to unlink.
            right_id: Identifier of the right entity to unlink.
        """
        self.add_command(Unlink[L_ID, R_ID](left_id=left_id, right_id=right_id))
