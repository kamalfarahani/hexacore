from hexacore.entity import Entity

from ..base_relation import BaseRelation
from .commands import (
    Create,
    GetLeft,
    GetRight,
    Unlink,
    UpdateLeft,
    UpdateRight,
)


class OneToOne[L_ID, R_ID, L: Entity, R: Entity](BaseRelation):
    """Represents a one-to-one relationship between two entities.

    Methods append commands for later processing. They do not execute the
    operations or return retrieved entities.
    """

    def create(self, left_id: L_ID, right_id: R_ID) -> None:
        """Append a command to link the specified entities.

        Args:
            left_id: Identifier of the left entity to link.
            right_id: Identifier of the right entity to link.
        """
        self.add_command(
            Create[L_ID, R_ID](
                left_id=left_id,
                right_id=right_id,
            )
        )

    def get_left(self, right_id: R_ID) -> None:
        """Append a command to retrieve the left entity linked to a right entity.

        Args:
            right_id: Identifier of the right entity used to locate the left entity.
        """
        self.add_command(GetLeft[R_ID](right_id=right_id))

    def get_right(self, left_id: L_ID) -> None:
        """Append a command to retrieve the right entity linked to a left entity.

        Args:
            left_id: Identifier of the left entity used to locate the right entity.
        """
        self.add_command(GetRight[L_ID](left_id=left_id))

    def update_left(self, right_id: R_ID, left: L) -> None:
        """Append a command to update the left entity linked to a right entity.

        Args:
            right_id: Identifier of the right entity used to locate the left entity.
            left: Entity supplied for the left-side update.
        """
        self.add_command(
            UpdateLeft[R_ID, L](
                right_id=right_id,
                left=left,
            )
        )

    def update_right(self, left_id: L_ID, right: R) -> None:
        """Append a command to update the right entity linked to a left entity.

        Args:
            left_id: Identifier of the left entity used to locate the right entity.
            right: Entity supplied for the right-side update.
        """
        self.add_command(
            UpdateRight[L_ID, R](
                left_id=left_id,
                right=right,
            )
        )

    def unlink(self, left_id: L_ID, right_id: R_ID) -> None:
        """Append a command to remove the link between the specified entities.

        Args:
            left_id: Identifier of the left entity to unlink.
            right_id: Identifier of the right entity to unlink.
        """
        self.add_command(
            Unlink[L_ID, R_ID](
                left_id=left_id,
                right_id=right_id,
            )
        )
