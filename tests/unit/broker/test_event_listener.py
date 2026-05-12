import logging
from typing import Generator

import pytest

from hexacore.broker.connection.exceptions import ConsumeError
from hexacore.broker.event_listener import EventListener
from tests.fakes import FakeBrokerConnection


@pytest.fixture
def fake_connection() -> FakeBrokerConnection:
    return FakeBrokerConnection()


class TestListen:
    def test_yields_all_messages_from_queue(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        messages = [{"id": 1}, {"id": 2}, {"id": 3}]
        fake_connection.queues["q"] = messages

        listener = EventListener(fake_connection)
        received = list(listener.listen("q"))

        assert received == messages

    def test_passes_queue_name_to_connection(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        fake_connection.queues["my_queue"] = [{"x": 1}]
        listener = EventListener(fake_connection)

        list(listener.listen("my_queue"))

        assert fake_connection.consumed_queues == ["my_queue"]

    def test_returns_generator(self, fake_connection: FakeBrokerConnection) -> None:
        listener = EventListener(fake_connection)
        result = listener.listen("q")
        assert isinstance(result, Generator)

    def test_listen_is_lazy(self, fake_connection: FakeBrokerConnection) -> None:
        fake_connection.queues["q"] = [{"x": 1}]
        listener = EventListener(fake_connection)

        listener.listen("q")

        assert fake_connection.consumed_queues == []

    def test_empty_queue_yields_nothing(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        fake_connection.queues["q"] = []
        listener = EventListener(fake_connection)

        assert list(listener.listen("q")) == []

    def test_consume_error_is_swallowed_and_logged(
        self,
        fake_connection: FakeBrokerConnection,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_connection.consume_errors["q"] = ConsumeError("boom")
        listener = EventListener(fake_connection)

        with caplog.at_level(logging.ERROR, logger="hexacore.broker.event_listener"):
            received = list(listener.listen("q"))

        assert received == []
        assert any(
            "Error listening to queue q" in record.message
            and record.levelno == logging.ERROR
            for record in caplog.records
        )

    def test_consume_error_raised_mid_stream_swallowed(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        def flaky(queue_name: str) -> Generator[dict, None, None]:
            yield {"id": 1}
            raise ConsumeError("mid-stream")

        fake_connection.consume = flaky  # type: ignore[assignment]
        listener = EventListener(fake_connection)

        received = list(listener.listen("q"))

        assert received == [{"id": 1}]

    def test_non_consume_error_propagates(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        fake_connection.consume_errors["q"] = RuntimeError("unexpected")
        listener = EventListener(fake_connection)

        with pytest.raises(RuntimeError, match="unexpected"):
            list(listener.listen("q"))


class TestContextManager:
    def test_enter_opens_connection_and_returns_listener(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        listener = EventListener(fake_connection)

        with listener as entered:
            assert entered is listener
            assert fake_connection.is_open is True
            assert fake_connection.enter_calls == 1

    def test_exit_closes_connection(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        listener = EventListener(fake_connection)

        with listener:
            pass

        assert fake_connection.is_open is False
        assert fake_connection.exit_calls == 1
        assert fake_connection.last_exit_info == (None, None, None)

    def test_exit_forwards_exception_info_and_propagates(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        listener = EventListener(fake_connection)

        with pytest.raises(ValueError, match="kaboom"):
            with listener:
                raise ValueError("kaboom")

        assert fake_connection.exit_calls == 1
        exc_type, exc_val, exc_tb = fake_connection.last_exit_info  # type: ignore[misc]
        assert exc_type is ValueError
        assert isinstance(exc_val, ValueError)
        assert exc_tb is not None
        assert fake_connection.is_open is False

    def test_listen_inside_context_manager(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        fake_connection.queues["q"] = [{"a": 1}, {"a": 2}]
        listener = EventListener(fake_connection)

        with listener as entered:
            received = list(entered.listen("q"))

        assert received == [{"a": 1}, {"a": 2}]
        assert fake_connection.enter_calls == 1
        assert fake_connection.exit_calls == 1
