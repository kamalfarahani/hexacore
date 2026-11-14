from dataclasses import dataclass, field

import pytest
from katharos.types import ImmutableList

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent
from hexacore.message_bus.handler import BaseCommandHandler, BaseEventHandler

from tests.fakes import FakeHandleResult


class SampleCommand(BaseCommand):
    payload: str


class SampleEvent(BaseEvent):
    payload: str


@dataclass
class ApplicationContext:
    prefix: str
    received: list[BaseCommand | BaseEvent] = field(default_factory=list)


class ContextCommandHandler(BaseCommandHandler[SampleCommand, FakeHandleResult]):
    def __init__(self, context: ApplicationContext) -> None:
        self.context = context

    def handle(self, command: SampleCommand) -> FakeHandleResult:
        self.context.received.append(command)
        return FakeHandleResult(
            ImmutableList([SampleEvent(payload=self.context.prefix + command.payload)])
        )


class ContextEventHandler(BaseEventHandler[SampleEvent, FakeHandleResult]):
    def __init__(self, context: ApplicationContext) -> None:
        self.context = context

    def handle(self, event: SampleEvent) -> FakeHandleResult:
        self.context.received.append(event)
        return FakeHandleResult(
            ImmutableList([SampleEvent(payload=self.context.prefix + event.payload)])
        )


@pytest.mark.parametrize("call_handler", [False, True], ids=["handle", "call"])
def test_command_handler_manages_its_own_context(
    call_handler: bool,
) -> None:
    context = ApplicationContext(prefix="before:")
    handler = ContextCommandHandler(context)
    message = SampleCommand(payload="input")
    # Changes after construction remain visible to the handler.
    context.prefix = "after:"

    result = handler(message) if call_handler else handler.handle(message)

    assert handler.context is context
    assert context.received == [message]
    assert isinstance(result, FakeHandleResult)
    assert isinstance(result.events, ImmutableList)
    assert list(result.events) == [SampleEvent(payload="after:input")]


@pytest.mark.parametrize("call_handler", [False, True], ids=["handle", "call"])
def test_event_handler_manages_its_own_context(
    call_handler: bool,
) -> None:
    context = ApplicationContext(prefix="before:")
    handler = ContextEventHandler(context)
    message = SampleEvent(payload="input")
    # Changes after construction remain visible to the handler.
    context.prefix = "after:"

    result = handler(message) if call_handler else handler.handle(message)

    assert handler.context is context
    assert context.received == [message]
    assert isinstance(result, FakeHandleResult)
    assert isinstance(result.events, ImmutableList)
    assert list(result.events) == [SampleEvent(payload="after:input")]


class ApplicationResult(FakeHandleResult):
    """Carry application data alongside produced events."""

    def __init__(self, events: ImmutableList[BaseEvent], reference: str) -> None:
        super().__init__(events)
        self.reference = reference


class FixedCommandHandler(BaseCommandHandler[SampleCommand, ApplicationResult]):
    """Return a preconstructed application result unchanged."""

    def __init__(self, result: ApplicationResult) -> None:
        self.result = result

    def handle(self, command: SampleCommand) -> ApplicationResult:
        return self.result


class FixedEventHandler(BaseEventHandler[SampleEvent, ApplicationResult]):
    """Return a preconstructed application result unchanged."""

    def __init__(self, result: ApplicationResult) -> None:
        self.result = result

    def handle(self, event: SampleEvent) -> ApplicationResult:
        return self.result


@pytest.mark.parametrize("call_handler", [False, True], ids=["handle", "call"])
def test_command_handler_preserves_application_result_identity(
    call_handler: bool,
) -> None:
    events: ImmutableList[BaseEvent] = ImmutableList([SampleEvent(payload="output")])
    expected = ApplicationResult(events, reference="command-result")
    handler = FixedCommandHandler(expected)
    command = SampleCommand(payload="input")

    result = handler(command) if call_handler else handler.handle(command)

    assert result is expected
    assert result.events is events
    assert result.reference == "command-result"


@pytest.mark.parametrize("call_handler", [False, True], ids=["handle", "call"])
def test_event_handler_preserves_application_result_identity(
    call_handler: bool,
) -> None:
    events: ImmutableList[BaseEvent] = ImmutableList([SampleEvent(payload="output")])
    expected = ApplicationResult(events, reference="event-result")
    handler = FixedEventHandler(expected)
    event = SampleEvent(payload="input")

    result = handler(event) if call_handler else handler.handle(event)

    assert result is expected
    assert result.events is events
    assert result.reference == "event-result"
