"""Define command payloads for operations on many-to-many relations."""

from hexacore.entity import Entity

from ..base_relation_command import BaseRelationCommand


class Create[L_ID, R_ID](BaseRelationCommand):
    """Request a link between one left entity and one right entity.

    Attributes:
        left_id: Identifier of the left entity to link.
        right_id: Identifier of the right entity to link.
    """

    left_id: L_ID
    right_id: R_ID


class GetLefts[R_ID](BaseRelationCommand):
    """Request all left entities linked to a specified right entity.

    Attributes:
        right_id: Identifier of the right entity whose left entities are requested.
    """

    right_id: R_ID


class GetRights[L_ID](BaseRelationCommand):
    """Request all right entities linked to a specified left entity.

    Attributes:
        left_id: Identifier of the left entity whose right entities are requested.
    """

    left_id: L_ID


class UpdateLeft[R_ID, L: Entity](BaseRelationCommand):
    """Request an update to one left entity linked to a specified right entity.

    Attributes:
        right_id: Identifier of the right entity associated with the left entity.
        left: Entity supplied for the update, with its identifier selecting
            the left entity within the relation.
    """

    right_id: R_ID
    left: L


class UpdateRight[L_ID, R: Entity](BaseRelationCommand):
    """Request an update to one right entity linked to a specified left entity.

    Attributes:
        left_id: Identifier of the left entity associated with the right entity.
        right: Entity supplied for the update, with its identifier selecting
            the right entity within the relation.
    """

    left_id: L_ID
    right: R


class Unlink[L_ID, R_ID](BaseRelationCommand):
    """Request removal of one link between a left entity and a right entity.

    Attributes:
        left_id: Identifier of the left entity to unlink.
        right_id: Identifier of the right entity to unlink.
    """

    left_id: L_ID
    right_id: R_ID
