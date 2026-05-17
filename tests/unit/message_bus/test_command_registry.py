import pytest
from katharos.types import ImmutableList

from hexacore.command import BaseCommand
from hexacore.event import BaseEvent
from hexacore.message_bus.handler import BaseCommandHandler
from hexacore.message_bus.registry import CommandRegistry


class CommandA(BaseCommand):
    pass


class CommandB(BaseCommand):
    pass


class FakeHandler(BaseCommandHandler):
    """A real, minimal handler used as a fake.

    Bypasses the parent ``__init__`` since these tests only care about the
    registry's storage/lookup behavior, not about how a handler executes.
    """

    def __init__(self, label: str) -> None:
        self.label = label

    def handle(self, command: BaseCommand) -> ImmutableList[BaseEvent]:
        return ImmutableList([])


class CountingDefaultFactory:
    """Default handler factory that records each call and returns a fresh handler."""

    def __init__(self) -> None:
        self.calls = 0
        self.produced: list[FakeHandler] = []

    def __call__(self) -> FakeHandler:
        self.calls += 1
        handler = FakeHandler(label=f"default-{self.calls}")
        self.produced.append(handler)
        return handler


@pytest.fixture
def default_factory() -> CountingDefaultFactory:
    return CountingDefaultFactory()


@pytest.fixture
def registry(default_factory: CountingDefaultFactory) -> CommandRegistry:
    return CommandRegistry(default_factory)


class TestInit:
    def test_does_not_invoke_factory(
        self,
        registry: CommandRegistry,
        default_factory: CountingDefaultFactory,
    ) -> None:
        assert default_factory.calls == 0


class TestGetItem:
    def test_unknown_key_produces_default_handler(
        self, registry: CommandRegistry, default_factory: CountingDefaultFactory
    ) -> None:
        handler = registry[CommandA]

        assert handler is default_factory.produced[0]
        assert default_factory.calls == 1

    def test_repeated_access_reuses_default_handler(
        self, registry: CommandRegistry, default_factory: CountingDefaultFactory
    ) -> None:
        first = registry[CommandA]
        second = registry[CommandA]

        assert first is second
        assert default_factory.calls == 1

    def test_different_keys_get_independent_defaults(
        self, registry: CommandRegistry, default_factory: CountingDefaultFactory
    ) -> None:
        handler_a = registry[CommandA]
        handler_b = registry[CommandB]

        assert handler_a is not handler_b
        assert default_factory.calls == 2


class TestSetItem:
    def test_stores_handler_for_command_type(self, registry: CommandRegistry) -> None:
        handler = FakeHandler(label="explicit")

        registry[CommandA] = handler

        assert registry[CommandA] is handler

    def test_set_does_not_invoke_default_factory(
        self,
        registry: CommandRegistry,
        default_factory: CountingDefaultFactory,
    ) -> None:
        registry[CommandA] = FakeHandler(label="explicit")

        assert default_factory.calls == 0

    def test_overrides_previously_registered_handler(
        self, registry: CommandRegistry
    ) -> None:
        first = FakeHandler(label="first")
        second = FakeHandler(label="second")

        registry[CommandA] = first
        registry[CommandA] = second

        assert registry[CommandA] is second

    def test_overrides_default_handler_for_key(
        self,
        registry: CommandRegistry,
        default_factory: CountingDefaultFactory,
    ) -> None:
        # Trigger default creation first.
        registry[CommandA]
        assert default_factory.calls == 1

        explicit = FakeHandler(label="explicit")
        registry[CommandA] = explicit

        assert registry[CommandA] is explicit
        # No new default produced on lookup.
        assert default_factory.calls == 1

    def test_setting_one_key_does_not_affect_others(
        self, registry: CommandRegistry
    ) -> None:
        handler_a = FakeHandler(label="A")
        registry[CommandA] = handler_a

        handler_b = registry[CommandB]

        assert handler_b is not handler_a
        assert registry[CommandA] is handler_a
