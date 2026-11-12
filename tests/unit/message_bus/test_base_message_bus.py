from collections.abc import Sequence

import pytest
from katharos.types import ImmutableList

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent
from hexacore.message_bus.base_message_bus import BaseMessageBus
from hexacore.message_bus.extension import Extension, HandlerPair
from hexacore.message_bus.handler import (
    BaseCommandHandler,
    BaseEventHandler,
    NoOpCommandHandler,
)
from hexacore.message_bus.registry import CommandRegistry, EventRegistry

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


class RecordingCommandHandler(BaseCommandHandler[BaseCommand]):
    def __init__(
        self,
        produced_events: Sequence[BaseEvent] | None = None,
    ) -> None:
        self.received: list[BaseCommand] = []
        self._produced = produced_events or []

    def handle(self, command: BaseCommand) -> ImmutableList[BaseEvent]:
        self.received.append(command)
        return ImmutableList(list(self._produced))


class RecordingEventHandler(BaseEventHandler[BaseEvent]):
    def __init__(
        self,
        produced_events: Sequence[BaseEvent] | None = None,
    ) -> None:
        self.received: list[BaseEvent] = []
        self._produced = produced_events or []

    def handle(self, event: BaseEvent) -> ImmutableList[BaseEvent]:
        self.received.append(event)
        return ImmutableList(list(self._produced))


class CommandAHandler(BaseCommandHandler[CommandA]):
    """Turn a command payload into an event to exercise specialized handlers."""

    def handle(self, command: CommandA) -> ImmutableList[BaseEvent]:
        return ImmutableList([EventX(payload=command.payload)])


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def command_registry() -> CommandRegistry:
    return CommandRegistry(NoOpCommandHandler)


@pytest.fixture
def event_registry() -> EventRegistry:
    return EventRegistry(list)


@pytest.fixture
def bus(
    command_registry: CommandRegistry,
    event_registry: EventRegistry,
) -> BaseMessageBus:
    return BaseMessageBus(command_registry, event_registry)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestInit:
    def test_stores_dependencies(
        self,
        bus: BaseMessageBus,
        command_registry: CommandRegistry,
        event_registry: EventRegistry,
    ) -> None:
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

        result = bus.handle(command)

        assert handler.received == [command]
        assert isinstance(result, ImmutableList)
        assert list(result) == []

    def test_handle_event_only_entry(
        self,
        bus: BaseMessageBus,
        event_registry: EventRegistry,
    ) -> None:
        handler = RecordingEventHandler()
        event_registry[EventX] = [handler]
        event = EventX()

        result = bus.handle(event)

        assert handler.received == [event]
        assert isinstance(result, ImmutableList)
        assert list(result) == [event]

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
            def handle(self, command: BaseCommand) -> ImmutableList[BaseEvent]:
                order.append(type(command))
                return super().handle(command)

        class TrackingEventHandler(RecordingEventHandler):
            def handle(self, event: BaseEvent) -> ImmutableList[BaseEvent]:
                order.append(type(event))
                return super().handle(event)

        event_x = EventX()
        event_y = EventY()
        event_z = EventZ()
        command_registry[CommandA] = TrackingCommandHandler(
            produced_events=[event_x, event_y]
        )
        event_registry[EventX] = [TrackingEventHandler(produced_events=[event_z])]
        event_registry[EventY] = [TrackingEventHandler()]
        event_registry[EventZ] = [TrackingEventHandler()]

        result = bus.handle(CommandA())

        assert order == [CommandA, EventX, EventY, EventZ]
        assert isinstance(result, ImmutableList)
        assert list(result) == [event_x, event_y, event_z]

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


class TestInstallExtension:
    def test_installs_multiple_handlers(
        self,
        bus: BaseMessageBus,
    ) -> None:
        handler_a = CommandAHandler()
        handler_b = RecordingCommandHandler(produced_events=[EventY()])
        extension = Extension(
            ImmutableList(
                [
                    HandlerPair(CommandA, handler_a),
                    HandlerPair(CommandB, handler_b),
                ]
            )
        )

        bus.install_extension(extension)
        result_a = bus.handle_command(CommandA(payload="installed"))
        command_b = CommandB()
        result_b = bus.handle_command(command_b)

        assert list(result_a) == [EventX(payload="installed")]
        assert list(result_b) == [EventY()]
        assert handler_b.received == [command_b]

    def test_dispatches_events_from_installed_handler(
        self,
        bus: BaseMessageBus,
        event_registry: EventRegistry,
    ) -> None:
        event_handler = RecordingEventHandler(produced_events=[EventY()])
        event_registry[EventX] = [event_handler]
        bus.install_extension(
            Extension(ImmutableList([HandlerPair(CommandA, CommandAHandler())]))
        )

        result = bus.handle(CommandA(payload="cascade"))

        assert list(result) == [EventX(payload="cascade"), EventY()]
        assert event_handler.received == [EventX(payload="cascade")]

    @pytest.mark.parametrize("registration", ["explicit", "default", "extension"])
    def test_replaces_existing_handler_and_preserves_other_commands(
        self,
        bus: BaseMessageBus,
        command_registry: CommandRegistry,
        registration: str,
    ) -> None:
        original: BaseCommandHandler[BaseCommand] = RecordingCommandHandler(
            produced_events=[EventZ()]
        )
        match registration:
            case "explicit":
                command_registry[CommandA] = original
            case "default":
                original = command_registry[CommandA]
            case "extension":
                bus.install_extension(
                    Extension(ImmutableList([HandlerPair(CommandA, original)]))
                )
        other = RecordingCommandHandler(produced_events=[EventY()])
        command_registry[CommandB] = other

        bus.install_extension(
            Extension(ImmutableList([HandlerPair(CommandA, CommandAHandler())]))
        )

        assert list(bus.handle_command(CommandA(payload="replacement"))) == [
            EventX(payload="replacement")
        ]
        assert command_registry[CommandA] is not original
        assert command_registry[CommandB] is other
        assert list(bus.handle_command(CommandB())) == [EventY()]

    def test_last_pair_wins_for_duplicate_command_types(
        self,
        bus: BaseMessageBus,
    ) -> None:
        first = RecordingCommandHandler(produced_events=[EventZ()])
        bus.install_extension(
            Extension(
                ImmutableList(
                    [
                        HandlerPair(CommandA, first),
                        HandlerPair(CommandA, CommandAHandler()),
                    ]
                )
            )
        )

        result = bus.handle_command(CommandA(payload="last"))

        assert list(result) == [EventX(payload="last")]
        assert first.received == []

    def test_empty_extension_preserves_existing_handlers(
        self,
        bus: BaseMessageBus,
        command_registry: CommandRegistry,
    ) -> None:
        handler = CommandAHandler()
        command_registry[CommandA] = handler

        bus.install_extension(Extension(ImmutableList([])))

        assert command_registry[CommandA] is handler
        assert list(bus.handle_command(CommandA(payload="unchanged"))) == [
            EventX(payload="unchanged")
        ]
