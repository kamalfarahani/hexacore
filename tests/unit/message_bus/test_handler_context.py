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


class ContextCommandHandler(BaseCommandHandler[SampleCommand]):
    def __init__(self, context: ApplicationContext) -> None:
        self.context = context

    def handle(self, command: SampleCommand) -> ImmutableList[BaseEvent]:
        self.context.received.append(command)
        return ImmutableList(
            [SampleEvent(payload=self.context.prefix + command.payload)]
        )


class ContextEventHandler(BaseEventHandler[SampleEvent]):
    def __init__(self, context: ApplicationContext) -> None:
        self.context = context

    def handle(self, event: SampleEvent) -> ImmutableList[BaseEvent]:
        self.context.received.append(event)
        return ImmutableList(
            [SampleEvent(payload=self.context.prefix + event.payload)]
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
    assert isinstance(result, ImmutableList)
    assert list(result) == [SampleEvent(payload="after:input")]


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
    assert isinstance(result, ImmutableList)
    assert list(result) == [SampleEvent(payload="after:input")]
