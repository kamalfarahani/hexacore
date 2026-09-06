"""Define mutations representing changes to many-to-many relations."""

from hexacore.entity import Entity

from ..base_relation_mutation import BaseRelationMutation


class Create[L_ID, R_ID](BaseRelationMutation):
    """Represent adding a link between one left entity and one right entity.

    Attributes:
        left_id: Identifier of the left entity to link.
        right_id: Identifier of the right entity to link.
    """

    left_id: L_ID
    right_id: R_ID


class UpdateLeft[R_ID, L: Entity](BaseRelationMutation):
    """Represent changing one left entity linked to a specified right entity.

    Attributes:
        right_id: Identifier of the right entity associated with the left entity.
        left: Entity supplied for the update, with its identifier selecting
            the left entity within the relation.
    """

    right_id: R_ID
    left: L


class UpdateRight[L_ID, R: Entity](BaseRelationMutation):
    """Represent changing one right entity linked to a specified left entity.

    Attributes:
        left_id: Identifier of the left entity associated with the right entity.
        right: Entity supplied for the update, with its identifier selecting
            the right entity within the relation.
    """

    left_id: L_ID
    right: R


class Unlink[L_ID, R_ID](BaseRelationMutation):
    """Represent removing one link between a left entity and a right entity.

    Attributes:
        left_id: Identifier of the left entity to unlink.
        right_id: Identifier of the right entity to unlink.
    """

    left_id: L_ID
    right_id: R_ID
