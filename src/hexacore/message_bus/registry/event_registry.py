"""Handler registry for events."""

from collections import defaultdict
from collections.abc import Callable
from typing import cast

from katharos.types import ImmutableList

from hexacore.event import BaseEvent
from hexacore.message_bus.handler import BaseEventHandler, BaseHandleResult


class EventRegistry:
    """Map exact event types to immutable handler lists, creating defaults on lookup."""

    def __init__(
        self,
        default_handler_factory: Callable[
            [], ImmutableList[BaseEventHandler[BaseEvent, BaseHandleResult]]
        ],
    ) -> None:
        """Initialize the event registry with a default handler factory.

        Args:
            default_handler_factory: A factory that returns an immutable list of
                event handlers when an event type has no registered handlers.
                Default handlers must support every event type.
        """
        self._registry: defaultdict[type[BaseEvent], object] = defaultdict(
            default_handler_factory
        )

    def __getitem__[E: BaseEvent](
        self,
        key: type[E],
    ) -> ImmutableList[BaseEventHandler[E, BaseHandleResult]]:
        """Retrieve the list of event handlers associated with the given event type.

        Args:
            key: The event type for which to retrieve handlers.

        Returns:
            The stored immutable handler list, creating and storing a default
            immutable list if the event type is missing.
        """
        # Registration preserves the relationship between each key and handlers.
        return cast(
            ImmutableList[BaseEventHandler[E, BaseHandleResult]], self._registry[key]
        )

    def __setitem__[E: BaseEvent](
        self,
        key: type[E],
        value: ImmutableList[BaseEventHandler[E, BaseHandleResult]],
    ) -> None:
        """Associate an immutable handler list with a specific event type.

        Args:
            key: The event type to associate with the handlers.
            value: The event handlers to associate with the event type.
        """
        self._registry[key] = value
