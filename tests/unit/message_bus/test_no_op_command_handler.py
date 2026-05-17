import logging

import pytest
from katharos.types import ImmutableList

from hexacore.broker.event_publisher import EventPublisher
from hexacore.command import BaseCommand
from hexacore.message_bus.handler.handle_context import HandleContext
from hexacore.message_bus.handler.no_op_command_handler import NoOpCommandHandler
from tests.fakes import FakeBrokerConnection


class SampleCommand(BaseCommand):
    payload: str


@pytest.fixture
def handle_context() -> HandleContext:
    # NoOpCommandHandler never touches the context, but BaseCommandHandler
    # requires one. We pass real, minimal collaborators rather than mocks.
    def uow_factory(ModelType):  # pragma: no cover - never called
        raise AssertionError("unit_of_work_factory should not be called")

    return HandleContext(
        unit_of_work_factory=uow_factory,
        event_publisher=EventPublisher(FakeBrokerConnection()),
    )


@pytest.fixture
def handler(handle_context: HandleContext) -> NoOpCommandHandler:
    return NoOpCommandHandler(handle_context)


class TestHandle:
    def test_returns_empty_immutable_list(self, handler: NoOpCommandHandler) -> None:
        result = handler.handle(SampleCommand(payload="x"))

        assert isinstance(result, ImmutableList)
        assert list(result) == []

    def test_logs_warning_with_command(
        self,
        handler: NoOpCommandHandler,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        command = SampleCommand(payload="hello")

        with caplog.at_level(
            logging.WARNING,
            logger="hexacore.message_bus.handler.no_op_command_handler",
        ):
            handler.handle(command)

        assert any(
            record.levelno == logging.WARNING
            and "No operation for command" in record.getMessage()
            and "hello" in record.getMessage()
            for record in caplog.records
        )

    def test_returns_fresh_list_each_call(self, handler: NoOpCommandHandler) -> None:
        first = handler.handle(SampleCommand(payload="a"))
        second = handler.handle(SampleCommand(payload="b"))

        assert list(first) == []
        assert list(second) == []


class TestCall:
    def test_call_delegates_to_handle(self, handler: NoOpCommandHandler) -> None:
        result = handler(SampleCommand(payload="x"))

        assert isinstance(result, ImmutableList)
        assert list(result) == []


class TestInit:
    def test_stores_handle_context(
        self,
        handler: NoOpCommandHandler,
        handle_context: HandleContext,
    ) -> None:
        assert handler.handle_context is handle_context
