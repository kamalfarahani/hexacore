import json

import pytest

from hexacore.broker.connection.exceptions import (
    ConsumeError,
    OpenError,
    PublishError,
)
from hexacore.broker.connection.rabbitmq import RabbitMQConnection

# ---------------------------------------------------------------------------
# Connection lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    def test_open_sets_connection_pair(
        self, closed_connection: RabbitMQConnection
    ) -> None:
        closed_connection.open()
        try:
            assert closed_connection._connection_pair is not None
            connection, channel = closed_connection._connection_pair
            assert connection.is_open
            assert channel.is_open
        finally:
            closed_connection.close()

    def test_double_open_raises(self, connection: RabbitMQConnection) -> None:
        with pytest.raises(OpenError):
            connection.open()

    def test_close_resets_state(self, closed_connection: RabbitMQConnection) -> None:
        closed_connection.open()
        pair = closed_connection._connection_pair
        assert pair is not None
        closed_connection.close()
        assert closed_connection._connection_pair is None
        connection, channel = pair
        assert not connection.is_open
        assert not channel.is_open

    def test_close_without_open_is_noop(
        self, closed_connection: RabbitMQConnection
    ) -> None:
        closed_connection.close()
        assert closed_connection._connection_pair is None

    def test_double_close_is_noop(self, closed_connection: RabbitMQConnection) -> None:
        closed_connection.open()
        closed_connection.close()
        closed_connection.close()
        assert closed_connection._connection_pair is None

    def test_reopen_after_close(
        self, closed_connection: RabbitMQConnection, unique_name: str
    ) -> None:
        closed_connection.open()
        closed_connection.close()
        closed_connection.open()
        try:
            closed_connection.create_queue(unique_name, durable=False)
        finally:
            _cleanup_queue(closed_connection, unique_name)
            closed_connection.close()

    def test_context_manager(
        self, closed_connection: RabbitMQConnection, unique_name: str
    ) -> None:
        with closed_connection as conn:
            assert conn is closed_connection
            assert closed_connection._connection_pair is not None
            conn.create_queue(unique_name, durable=False)
            _cleanup_queue(conn, unique_name)
        assert closed_connection._connection_pair is None


# ---------------------------------------------------------------------------
# Operations on a closed connection raise OpenError
# ---------------------------------------------------------------------------


class TestOperationsRequireOpen:
    def test_create_queue_requires_open(
        self, closed_connection: RabbitMQConnection, unique_name: str
    ) -> None:
        with pytest.raises(OpenError):
            closed_connection.create_queue(unique_name)

    def test_create_exchange_requires_open(
        self, closed_connection: RabbitMQConnection, unique_name: str
    ) -> None:
        with pytest.raises(OpenError):
            closed_connection.create_exchange(unique_name)

    def test_bind_queue_requires_open(
        self, closed_connection: RabbitMQConnection, unique_name: str
    ) -> None:
        with pytest.raises(OpenError):
            closed_connection.bind_queue(unique_name, unique_name, "rk")

    def test_publish_wraps_open_error(
        self, closed_connection: RabbitMQConnection, unique_name: str
    ) -> None:
        # publish catches all exceptions and re-raises as PublishError,
        # so the OpenError from _get_channel is wrapped.
        with pytest.raises(PublishError):
            closed_connection.publish(unique_name, "rk", {"a": 1})

    def test_consume_is_lazy_then_raises(
        self, closed_connection: RabbitMQConnection, unique_name: str
    ) -> None:
        gen = closed_connection.consume(unique_name)
        with pytest.raises(ConsumeError):
            next(gen)


# ---------------------------------------------------------------------------
# create_queue
# ---------------------------------------------------------------------------


class TestCreateQueue:
    def test_declares_queue(
        self, connection: RabbitMQConnection, unique_name: str
    ) -> None:
        connection.create_queue(unique_name, durable=False)
        # Passive redeclare should succeed if it exists.
        connection._get_channel().queue_declare(queue=unique_name, passive=True)
        _cleanup_queue(connection, unique_name)

    def test_declare_is_idempotent(
        self, connection: RabbitMQConnection, unique_name: str
    ) -> None:
        connection.create_queue(unique_name, durable=False)
        connection.create_queue(unique_name, durable=False)
        _cleanup_queue(connection, unique_name)

    def test_durable_queue_survives_reconnect(
        self,
        closed_connection: RabbitMQConnection,
        connection_parameters,
        unique_name: str,
    ) -> None:
        closed_connection.open()
        closed_connection.create_queue(unique_name, durable=True)
        closed_connection.close()

        other = RabbitMQConnection(connection_parameters)
        other.open()
        try:
            # Passive declare succeeds only if the queue still exists.
            other._get_channel().queue_declare(queue=unique_name, passive=True)
        finally:
            _cleanup_queue(other, unique_name)
            other.close()


# ---------------------------------------------------------------------------
# create_exchange
# ---------------------------------------------------------------------------


class TestCreateExchange:
    @pytest.mark.parametrize("exchange_type", ["direct", "fanout", "topic", "headers"])
    def test_declares_each_exchange_type(
        self,
        connection: RabbitMQConnection,
        unique_name: str,
        exchange_type: str,
    ) -> None:
        connection.create_exchange(
            unique_name, exchange_type=exchange_type, durable=False
        )
        _cleanup_exchange(connection, unique_name)

    def test_idempotent_same_args(
        self, connection: RabbitMQConnection, unique_name: str
    ) -> None:
        connection.create_exchange(unique_name, "direct", durable=False)
        connection.create_exchange(unique_name, "direct", durable=False)
        _cleanup_exchange(connection, unique_name)


# ---------------------------------------------------------------------------
# bind_queue
# ---------------------------------------------------------------------------


class TestBindQueue:
    def test_binding_routes_messages(
        self, connection: RabbitMQConnection, unique_name: str
    ) -> None:
        queue = f"{unique_name}-q"
        exchange = f"{unique_name}-x"
        rk = "route.key"

        connection.create_exchange(exchange, "direct", durable=False)
        connection.create_queue(queue, durable=False)
        connection.bind_queue(queue, exchange, rk)
        connection.publish(exchange, rk, {"hello": "world"})

        message = _get_one(connection, queue)
        assert message is not None
        assert json.loads(message["body"]) == {"hello": "world"}

        _cleanup_queue(connection, queue)
        _cleanup_exchange(connection, exchange)

    def test_fanout_with_empty_routing_key(
        self, connection: RabbitMQConnection, unique_name: str
    ) -> None:
        queue = f"{unique_name}-q"
        exchange = f"{unique_name}-x"

        connection.create_exchange(exchange, "fanout", durable=False)
        connection.create_queue(queue, durable=False)
        connection.bind_queue(queue, exchange, "")
        connection.publish(exchange, "", {"n": 1})

        message = _get_one(connection, queue)
        assert message is not None
        assert json.loads(message["body"]) == {"n": 1}

        _cleanup_queue(connection, queue)
        _cleanup_exchange(connection, exchange)

    def test_unbound_queue_receives_nothing(
        self, connection: RabbitMQConnection, unique_name: str
    ) -> None:
        queue = f"{unique_name}-q"
        exchange = f"{unique_name}-x"

        connection.create_exchange(exchange, "direct", durable=False)
        connection.create_queue(queue, durable=False)
        # No bind on purpose.
        connection.publish(exchange, "anything", {"n": 1})

        message = _get_one(connection, queue)
        assert message is None

        _cleanup_queue(connection, queue)
        _cleanup_exchange(connection, exchange)


# ---------------------------------------------------------------------------
# publish
# ---------------------------------------------------------------------------


class TestPublish:
    def test_round_trip_preserves_payload(
        self, connection: RabbitMQConnection, unique_name: str
    ) -> None:
        queue, exchange, rk = _setup_direct(connection, unique_name)

        payload = {"a": 1, "b": [1, 2, 3], "c": {"nested": True}}
        connection.publish(exchange, rk, payload)

        message = _get_one(connection, queue)
        assert message is not None
        assert json.loads(message["body"]) == payload

        _cleanup_queue(connection, queue)
        _cleanup_exchange(connection, exchange)

    def test_non_serializable_data_raises_publish_error(
        self, connection: RabbitMQConnection, unique_name: str
    ) -> None:
        queue, exchange, rk = _setup_direct(connection, unique_name)
        with pytest.raises(PublishError):
            connection.publish(exchange, rk, {"bad": object()})
        _cleanup_queue(connection, queue)
        _cleanup_exchange(connection, exchange)

    def test_preserves_fifo_order(
        self, connection: RabbitMQConnection, unique_name: str
    ) -> None:
        queue, exchange, rk = _setup_direct(connection, unique_name)

        for i in range(5):
            connection.publish(exchange, rk, {"i": i})

        received = []
        for msg in connection.consume(queue):
            received.append(json.loads(msg["body"]))
            if len(received) == 5:
                break

        assert received == [{"i": i} for i in range(5)]

        _cleanup_queue(connection, queue)
        _cleanup_exchange(connection, exchange)


# ---------------------------------------------------------------------------
# consume
# ---------------------------------------------------------------------------


class TestConsume:
    def test_yields_message_dict_shape(
        self, connection: RabbitMQConnection, unique_name: str
    ) -> None:
        queue, exchange, rk = _setup_direct(connection, unique_name)
        connection.publish(exchange, rk, {"x": 1})

        message = _get_one(connection, queue)
        assert message is not None
        assert set(message.keys()) == {"method_frame", "header_frame", "body"}
        assert isinstance(message["body"], (bytes, bytearray))

        _cleanup_queue(connection, queue)
        _cleanup_exchange(connection, exchange)

    def test_auto_ack_removes_messages(
        self, connection: RabbitMQConnection, unique_name: str
    ) -> None:
        queue, exchange, rk = _setup_direct(connection, unique_name)
        connection.publish(exchange, rk, {"x": 1})

        first = _get_one(connection, queue)
        assert first is not None

        # After auto-ack consume, queue should be empty.
        result = connection._get_channel().queue_declare(
            queue=queue, durable=False, passive=True
        )
        assert result.method.message_count == 0

        _cleanup_queue(connection, queue)
        _cleanup_exchange(connection, exchange)

    def test_consume_nonexistent_queue_raises_consume_error(
        self,
        closed_connection: RabbitMQConnection,
        connection_parameters,
        unique_name: str,
    ) -> None:
        # Use a dedicated connection because a channel-level error closes the
        # channel for the rest of the test.
        closed_connection.open()
        try:
            gen = closed_connection.consume(unique_name)
            with pytest.raises(ConsumeError):
                next(gen)
        finally:
            closed_connection.close()

    def test_generator_cleanup_cancels_consumer(
        self, connection: RabbitMQConnection, unique_name: str
    ) -> None:
        queue, exchange, rk = _setup_direct(connection, unique_name)
        connection.publish(exchange, rk, {"x": 1})

        gen = connection.consume(queue)
        msg = next(gen)
        assert msg is not None
        gen.close()  # triggers the finally block -> channel.cancel()

        # Channel should still be usable for other operations.
        connection.create_queue(f"{unique_name}-after", durable=False)
        _cleanup_queue(connection, f"{unique_name}-after")
        _cleanup_queue(connection, queue)
        _cleanup_exchange(connection, exchange)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_direct(
    connection: RabbitMQConnection, unique_name: str
) -> tuple[str, str, str]:
    queue = f"{unique_name}-q"
    exchange = f"{unique_name}-x"
    rk = "rk"
    connection.create_exchange(exchange, "direct", durable=False)
    connection.create_queue(queue, durable=False)
    connection.bind_queue(queue, exchange, rk)
    return queue, exchange, rk


def _get_one(connection: RabbitMQConnection, queue: str) -> dict | None:
    """Pull a single message from a queue using basic_get (non-blocking)."""
    # Allow broker a brief moment to route the message.
    import time

    for _ in range(20):
        method, header, body = connection._get_channel().basic_get(
            queue=queue, auto_ack=True
        )
        if method is not None:
            return {
                "method_frame": method,
                "header_frame": header,
                "body": body,
            }
        time.sleep(0.05)
    return None


def _cleanup_queue(connection: RabbitMQConnection, queue: str) -> None:
    try:
        connection._get_channel().queue_delete(queue=queue)
    except Exception:
        pass


def _cleanup_exchange(connection: RabbitMQConnection, exchange: str) -> None:
    try:
        connection._get_channel().exchange_delete(exchange=exchange)
    except Exception:
        pass
