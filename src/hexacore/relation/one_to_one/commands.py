from hexacore.entity import Entity

from ..base_relation_command import BaseRelationCommand


class Create[L_ID, R_ID](BaseRelationCommand):
    """Request a link between a left entity and a right entity.

    Attributes:
        left_id: Identifier of the left entity to link.
        right_id: Identifier of the right entity to link.
    """

    left_id: L_ID
    right_id: R_ID


class GetLeft[L_ID](BaseRelationCommand):
    """Request the left entity linked to a specified right entity.

    Attributes:
        right_id: Identifier of the right entity used to locate the left entity.
    """

    right_id: L_ID


class GetRight[R_ID](BaseRelationCommand):
    """Request the right entity linked to a specified left entity.

    Attributes:
        left_id: Identifier of the left entity used to locate the right entity.
    """

    left_id: R_ID


class UpdateLeft[R_ID, L: Entity](BaseRelationCommand):
    """Request an update to the left entity linked to a specified right entity.

    Attributes:
        right_id: Identifier of the right entity used to locate the left entity.
        left: Entity supplied for the left-side update.
    """

    right_id: R_ID
    left: L


class UpdateRight[L_ID, R: Entity](BaseRelationCommand):
    """Request an update to the right entity linked to a specified left entity.

    Attributes:
        left_id: Identifier of the left entity used to locate the right entity.
        right: Entity supplied for the right-side update.
    """

    left_id: L_ID
    right: R


class Unlink[L_ID, R_ID](BaseRelationCommand):
    """Request removal of the link between a left entity and a right entity.

    Attributes:
        left_id: Identifier of the left entity to unlink.
        right_id: Identifier of the right entity to unlink.
    """

    left_id: L_ID
    right_id: R_ID
