from dataclasses import dataclass, field

import pytest
from katharos.types import ImmutableList

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent
from hexacore.message_bus.handler import BaseCommandHandler, BaseEventHandler


class SampleCommand(BaseCommand):
    payload: str


class SampleEvent(BaseEvent):
    payload: str


@dataclass
class ApplicationContext:
    prefix: str
    received: list[BaseCommand | BaseEvent] = field(default_factory=list)


class ContextCommandHandler(BaseCommandHandler[SampleCommand, ApplicationContext]):
    def handle(self, command: SampleCommand) -> ImmutableList[BaseEvent]:
        self.handle_context.received.append(command)
        return ImmutableList(
            [SampleEvent(payload=self.handle_context.prefix + command.payload)]
        )


class ContextEventHandler(BaseEventHandler[SampleEvent, ApplicationContext]):
    def handle(self, event: SampleEvent) -> ImmutableList[BaseEvent]:
        self.handle_context.received.append(event)
        return ImmutableList(
            [SampleEvent(payload=self.handle_context.prefix + event.payload)]
        )


@pytest.mark.parametrize("call_handler", [False, True], ids=["handle", "call"])
def test_command_handler_uses_application_context(
    call_handler: bool,
) -> None:
    context = ApplicationContext(prefix="before:")
    handler = ContextCommandHandler(context)
    message = SampleCommand(payload="input")
    # Changes after construction remain visible to the handler.
    context.prefix = "after:"

    result = handler(message) if call_handler else handler.handle(message)

    assert handler.handle_context is context
    assert context.received == [message]
    assert isinstance(result, ImmutableList)
    assert list(result) == [SampleEvent(payload="after:input")]


@pytest.mark.parametrize("call_handler", [False, True], ids=["handle", "call"])
def test_event_handler_uses_application_context(
    call_handler: bool,
) -> None:
    context = ApplicationContext(prefix="before:")
    handler = ContextEventHandler(context)
    message = SampleEvent(payload="input")
    # Changes after construction remain visible to the handler.
    context.prefix = "after:"

    result = handler(message) if call_handler else handler.handle(message)

    assert handler.handle_context is context
    assert context.received == [message]
    assert isinstance(result, ImmutableList)
    assert list(result) == [SampleEvent(payload="after:input")]
