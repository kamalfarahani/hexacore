import pytest
from katharos.types import ImmutableList

from hexacore.broker.event_publisher import EventPublisher
from hexacore.command import BaseCommand
from hexacore.event import BaseEvent
from hexacore.message_bus.base_message_bus import BaseMessageBus
from hexacore.message_bus.handler import (
    BaseCommandHandler,
    BaseEventHandler,
    HandleContext,
    NoOpCommandHandler,
)
from hexacore.message_bus.registry import CommandRegistry, EventRegistry
from tests.fakes import FakeBrokerConnection

# ---------------------------------------------------------------------------
# Test message types
# ---------------------------------------------------------------------------


class CommandA(BaseCommand):
    payload: str = ""


class CommandB(BaseCommand):
    pass


class EventX(BaseEvent):
    payload: str = ""


class EventY(BaseEvent):
    pass


class EventZ(BaseEvent):
    pass


class SubEventX(EventX):
    """Subclass of EventX, used to verify exact-type lookup semantics."""


# ---------------------------------------------------------------------------
# Recording handlers (real fakes — they really execute and produce events)
# ---------------------------------------------------------------------------


class RecordingCommandHandler(BaseCommandHandler):
    def __init__(
        self,
        produced_events: list[BaseEvent] | None = None,
    ) -> None:
        # Skip parent __init__: handle_context is not used in unit tests.
        self.received: list[BaseCommand] = []
        self._produced = produced_events or []

    def handle(self, command: BaseCommand) -> ImmutableList[BaseEvent]:
        self.received.append(command)
        return ImmutableList(list(self._produced))


class RecordingEventHandler(BaseEventHandler):
    def __init__(
        self,
        produced_events: list[BaseEvent] | None = None,
    ) -> None:
        self.received: list[BaseEvent] = []
        self._produced = produced_events or []

    def handle(self, event: BaseEvent) -> ImmutableList[BaseEvent]:
        self.received.append(event)
        return ImmutableList(list(self._produced))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def handle_context() -> HandleContext:
    def uow_factory(ModelType):  # pragma: no cover - never called in these tests
        raise AssertionError("unit_of_work_factory should not be called")

    return HandleContext(
        unit_of_work_factory=uow_factory,
        event_publisher=EventPublisher(FakeBrokerConnection()),
    )


@pytest.fixture
def command_registry(handle_context: HandleContext) -> CommandRegistry:
    return CommandRegistry(lambda: NoOpCommandHandler(handle_context))


@pytest.fixture
def event_registry() -> EventRegistry:
    return EventRegistry(list)


@pytest.fixture
def bus(
    handle_context: HandleContext,
    command_registry: CommandRegistry,
    event_registry: EventRegistry,
) -> BaseMessageBus:
    return BaseMessageBus(handle_context, command_registry, event_registry)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestInit:
    def test_stores_dependencies(
        self,
        bus: BaseMessageBus,
        handle_context: HandleContext,
        command_registry: CommandRegistry,
        event_registry: EventRegistry,
    ) -> None:
        assert bus._handle_context is handle_context
        assert bus._command_registry is command_registry
        assert bus._event_registry is event_registry


class TestHandleCommand:
    def test_dispatches_to_registered_handler(
        self,
        bus: BaseMessageBus,
        command_registry: CommandRegistry,
    ) -> None:
        handler = RecordingCommandHandler()
        command_registry[CommandA] = handler
        command = CommandA(payload="hi")

        result = bus.handle_command(command)

        assert handler.received == [command]
        assert list(result) == []

    def test_returns_events_produced_by_handler(
        self,
        bus: BaseMessageBus,
        command_registry: CommandRegistry,
    ) -> None:
        events = [EventX(payload="a"), EventY()]
        command_registry[CommandA] = RecordingCommandHandler(produced_events=events)

        result = bus.handle_command(CommandA())

        assert isinstance(result, ImmutableList)
        assert list(result) == events

    def test_unknown_command_uses_default_handler(
        self,
        bus: BaseMessageBus,
        command_registry: CommandRegistry,
    ) -> None:
        result = bus.handle_command(CommandB())

        # NoOpCommandHandler returns an empty list.
        assert list(result) == []
        # The default handler was materialized into the registry.
        assert isinstance(command_registry[CommandB], NoOpCommandHandler)

    def test_lookup_is_by_exact_type(
        self,
        bus: BaseMessageBus,
        command_registry: CommandRegistry,
    ) -> None:
        # A handler registered for CommandA must not be invoked for a
        # different command type.
        a_handler = RecordingCommandHandler(produced_events=[EventX()])
        command_registry[CommandA] = a_handler

        bus.handle_command(CommandB())

        assert a_handler.received == []


class TestHandleEvent:
    def test_dispatches_to_all_handlers_in_order(
        self,
        bus: BaseMessageBus,
        event_registry: EventRegistry,
    ) -> None:
        h1 = RecordingEventHandler()
        h2 = RecordingEventHandler()
        event_registry[EventX] = [h1, h2]
        event = EventX(payload="hello")

        bus.handle_event(event)

        assert h1.received == [event]
        assert h2.received == [event]

    def test_concatenates_events_from_all_handlers(
        self,
        bus: BaseMessageBus,
        event_registry: EventRegistry,
    ) -> None:
        h1 = RecordingEventHandler(produced_events=[EventY()])
        h2 = RecordingEventHandler(produced_events=[EventZ(), EventZ()])
        event_registry[EventX] = [h1, h2]

        result = bus.handle_event(EventX())

        assert isinstance(result, ImmutableList)
        assert [type(e) for e in result] == [EventY, EventZ, EventZ]

    def test_no_handlers_returns_empty_immutable_list(
        self,
        bus: BaseMessageBus,
    ) -> None:
        result = bus.handle_event(EventX())

        assert isinstance(result, ImmutableList)
        assert list(result) == []

    def test_lookup_is_by_exact_type(
        self,
        bus: BaseMessageBus,
        event_registry: EventRegistry,
    ) -> None:
        parent_handler = RecordingEventHandler()
        event_registry[EventX] = [parent_handler]

        bus.handle_event(SubEventX())

        assert parent_handler.received == []


class TestHandle:
    def test_handle_command_only(
        self,
        bus: BaseMessageBus,
        command_registry: CommandRegistry,
    ) -> None:
        handler = RecordingCommandHandler()
        command_registry[CommandA] = handler
        command = CommandA(payload="x")

        bus.handle(command)

        assert handler.received == [command]

    def test_handle_event_only_entry(
        self,
        bus: BaseMessageBus,
        event_registry: EventRegistry,
    ) -> None:
        handler = RecordingEventHandler()
        event_registry[EventX] = [handler]
        event = EventX()

        bus.handle(event)

        assert handler.received == [event]

    def test_command_emits_events_that_are_then_handled(
        self,
        bus: BaseMessageBus,
        command_registry: CommandRegistry,
        event_registry: EventRegistry,
    ) -> None:
        event_x = EventX()
        event_y = EventY()
        command_registry[CommandA] = RecordingCommandHandler(
            produced_events=[event_x, event_y]
        )
        x_handler = RecordingEventHandler()
        y_handler = RecordingEventHandler()
        event_registry[EventX] = [x_handler]
        event_registry[EventY] = [y_handler]

        bus.handle(CommandA())

        assert x_handler.received == [event_x]
        assert y_handler.received == [event_y]

    def test_full_cascade_in_fifo_order(
        self,
        bus: BaseMessageBus,
        command_registry: CommandRegistry,
        event_registry: EventRegistry,
    ) -> None:
        # CommandA -> [EventX, EventY]
        # EventX   -> [EventZ]
        # EventY   -> []
        # EventZ   -> []
        # Expected visit order: CommandA, EventX, EventY, EventZ
        order: list[type] = []

        class TrackingCommandHandler(RecordingCommandHandler):
            def handle(self, command):
                order.append(type(command))
                return super().handle(command)

        class TrackingEventHandler(RecordingEventHandler):
            def handle(self, event):
                order.append(type(event))
                return super().handle(event)

        command_registry[CommandA] = TrackingCommandHandler(
            produced_events=[EventX(), EventY()]
        )
        event_registry[EventX] = [TrackingEventHandler(produced_events=[EventZ()])]
        event_registry[EventY] = [TrackingEventHandler()]
        event_registry[EventZ] = [TrackingEventHandler()]

        bus.handle(CommandA())

        assert order == [CommandA, EventX, EventY, EventZ]

    def test_terminates_when_no_more_messages(
        self,
        bus: BaseMessageBus,
        command_registry: CommandRegistry,
    ) -> None:
        command_registry[CommandA] = RecordingCommandHandler()

        # Should return without hanging.
        bus.handle(CommandA())

    def test_does_not_re_handle_original_message(
        self,
        bus: BaseMessageBus,
        command_registry: CommandRegistry,
    ) -> None:
        handler = RecordingCommandHandler()
        command_registry[CommandA] = handler

        bus.handle(CommandA())

        assert len(handler.received) == 1

    def test_mixed_cascade_with_multiple_event_handlers(
        self,
        bus: BaseMessageBus,
        command_registry: CommandRegistry,
        event_registry: EventRegistry,
    ) -> None:
        # CommandA -> [EventX]
        # EventX   -> two handlers, each emitting one EventY
        # EventY   -> one handler emitting one EventZ
        command_registry[CommandA] = RecordingCommandHandler(produced_events=[EventX()])
        event_registry[EventX] = [
            RecordingEventHandler(produced_events=[EventY()]),
            RecordingEventHandler(produced_events=[EventY()]),
        ]
        y_handler = RecordingEventHandler(produced_events=[EventZ()])
        z_handler = RecordingEventHandler()
        event_registry[EventY] = [y_handler]
        event_registry[EventZ] = [z_handler]

        bus.handle(CommandA())

        # Two EventY were emitted (one per EventX handler), each producing
        # one EventZ.
        assert len(y_handler.received) == 2
        assert len(z_handler.received) == 2
