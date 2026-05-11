import logging

import pytest

from hexacore.broker.connection.exceptions import PublishError
from hexacore.broker.event_publisher import EventPublisher

from .fakes import FakeBrokerConnection


@pytest.fixture
def fake_connection() -> FakeBrokerConnection:
    return FakeBrokerConnection()


class TestPublish:
    def test_forwards_arguments_to_connection(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        publisher = EventPublisher(fake_connection)

        publisher.publish("ex", "rk", {"a": 1})

        assert fake_connection.published == [("ex", "rk", {"a": 1})]

    def test_publishes_multiple_messages_in_order(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        publisher = EventPublisher(fake_connection)

        for i in range(3):
            publisher.publish("ex", "rk", {"i": i})

        assert fake_connection.published == [
            ("ex", "rk", {"i": 0}),
            ("ex", "rk", {"i": 1}),
            ("ex", "rk", {"i": 2}),
        ]

    def test_returns_none(self, fake_connection: FakeBrokerConnection) -> None:
        publisher = EventPublisher(fake_connection)
        assert publisher.publish("ex", "rk", {"a": 1}) is None

    def test_publish_error_is_swallowed_and_logged(
        self,
        fake_connection: FakeBrokerConnection,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        fake_connection.publish_errors[("ex", "rk")] = PublishError("boom")
        publisher = EventPublisher(fake_connection)

        with caplog.at_level(logging.ERROR, logger="hexacore.broker.event_publisher"):
            publisher.publish("ex", "rk", {"a": 1})

        assert fake_connection.published == []
        assert any(
            "Error publishing to exchange ex" in record.message
            and record.levelno == logging.ERROR
            for record in caplog.records
        )

    def test_non_publish_error_propagates(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        fake_connection.publish_errors[("ex", "rk")] = RuntimeError("unexpected")
        publisher = EventPublisher(fake_connection)

        with pytest.raises(RuntimeError, match="unexpected"):
            publisher.publish("ex", "rk", {"a": 1})

    def test_publish_after_error_still_works(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        fake_connection.publish_errors[("ex", "bad")] = PublishError("boom")
        publisher = EventPublisher(fake_connection)

        publisher.publish("ex", "bad", {"a": 1})
        publisher.publish("ex", "good", {"a": 2})

        assert fake_connection.published == [("ex", "good", {"a": 2})]


class TestContextManager:
    def test_enter_opens_connection_and_returns_publisher(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        publisher = EventPublisher(fake_connection)

        with publisher as entered:
            assert entered is publisher
            assert fake_connection.is_open is True
            assert fake_connection.enter_calls == 1

    def test_exit_closes_connection(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        publisher = EventPublisher(fake_connection)

        with publisher:
            pass

        assert fake_connection.is_open is False
        assert fake_connection.exit_calls == 1
        assert fake_connection.last_exit_info == (None, None, None)

    def test_exit_forwards_exception_info_and_propagates(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        publisher = EventPublisher(fake_connection)

        with pytest.raises(ValueError, match="kaboom"):
            with publisher:
                raise ValueError("kaboom")

        assert fake_connection.exit_calls == 1
        exc_type, exc_val, exc_tb = fake_connection.last_exit_info  # type: ignore[misc]
        assert exc_type is ValueError
        assert isinstance(exc_val, ValueError)
        assert exc_tb is not None
        assert fake_connection.is_open is False

    def test_publish_inside_context_manager(
        self, fake_connection: FakeBrokerConnection
    ) -> None:
        publisher = EventPublisher(fake_connection)

        with publisher as entered:
            entered.publish("ex", "rk", {"a": 1})
            entered.publish("ex", "rk", {"a": 2})

        assert fake_connection.published == [
            ("ex", "rk", {"a": 1}),
            ("ex", "rk", {"a": 2}),
        ]
        assert fake_connection.enter_calls == 1
        assert fake_connection.exit_calls == 1
