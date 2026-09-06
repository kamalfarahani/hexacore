"""Define the base collector for relation mutations."""

from abc import ABC
from types import TracebackType
from typing import Self

from .base_relation_mutation import BaseRelationMutation


class BaseRelation(ABC):
    """Collect mutations representing changes to relations between entities."""

    _mutations: list[BaseRelationMutation]

    def __init__(self) -> None:
        """Initialize the relation without pending changes."""
        self._mutations = []

    def add_mutation(self, mutation: BaseRelationMutation) -> None:
        """Record a mutation describing a pending relation change.

        Args:
            mutation: Relation change to record.
        """
        self._mutations.append(mutation)

    @property
    def mutations(self) -> list[BaseRelationMutation]:
        """Pending relation changes in insertion order."""
        return self._mutations

    def __enter__(self) -> Self:
        """Discard pending changes and enter the relation context.

        Returns:
            This relation with no pending changes.
        """
        self._mutations = []
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit while preserving pending changes and propagating exceptions.

        Args:
            exc_type: Type of the exception raised in the context, or None if
                no exception occurred.
            exc_val: Exception instance, or None if no exception occurred.
            exc_tb: Exception traceback, or None if no exception occurred.
        """
