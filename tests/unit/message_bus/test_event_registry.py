import pytest
from katharos.types import ImmutableList

from hexacore.event import BaseEvent
from hexacore.message_bus.handler import BaseEventHandler
from hexacore.message_bus.registry import EventRegistry

from tests.fakes import FakeHandleResult


class EventA(BaseEvent):
    pass


class EventB(BaseEvent):
    pass


class FakeHandler(BaseEventHandler[BaseEvent, FakeHandleResult]):
    """Handle any event without producing further events."""

    def handle(self, event: BaseEvent) -> FakeHandleResult:
        return FakeHandleResult(ImmutableList([]))


class CountingDefaultFactory:
    """Return fresh immutable handler collections and record their creation."""

    def __init__(self) -> None:
        self.produced: list[ImmutableList[FakeHandler]] = []

    def __call__(self) -> ImmutableList[FakeHandler]:
        handlers = ImmutableList([FakeHandler()])
        self.produced.append(handlers)
        return handlers


@pytest.fixture
def default_factory() -> CountingDefaultFactory:
    return CountingDefaultFactory()


@pytest.fixture
def registry(default_factory: CountingDefaultFactory) -> EventRegistry:
    return EventRegistry(default_factory)


def test_init_does_not_invoke_factory(
    registry: EventRegistry, default_factory: CountingDefaultFactory
) -> None:
    assert default_factory.produced == []


def test_missing_type_creates_and_caches_immutable_handlers(
    registry: EventRegistry, default_factory: CountingDefaultFactory
) -> None:
    handlers = registry[EventA]

    assert isinstance(handlers, ImmutableList)
    assert registry[EventA] is handlers
    assert len(default_factory.produced) == 1
    assert handlers is default_factory.produced[0]


def test_different_types_get_independent_defaults(
    registry: EventRegistry, default_factory: CountingDefaultFactory
) -> None:
    first = registry[EventA]
    second = registry[EventB]

    assert first is not second
    assert len(default_factory.produced) == 2
    assert first[0] is not second[0]


def test_registration_preserves_collection_identity_and_order(
    registry: EventRegistry, default_factory: CountingDefaultFactory
) -> None:
    first = FakeHandler()
    second = FakeHandler()
    handlers = ImmutableList([first, second])

    registry[EventA] = handlers

    assert registry[EventA] is handlers
    assert registry[EventA][0] is first
    assert registry[EventA][1] is second
    assert default_factory.produced == []


@pytest.mark.parametrize("use_default", [False, True], ids=["explicit", "default"])
def test_registration_replaces_existing_handlers_and_preserves_other_types(
    registry: EventRegistry,
    default_factory: CountingDefaultFactory,
    use_default: bool,
) -> None:
    if use_default:
        original = registry[EventA]
    else:
        original = ImmutableList([FakeHandler()])
        registry[EventA] = original
    other = registry[EventB]
    calls_before = len(default_factory.produced)
    replacement = ImmutableList([FakeHandler()])

    registry[EventA] = replacement

    assert registry[EventA] is replacement
    assert registry[EventA] is not original
    assert registry[EventB] is other
    assert len(default_factory.produced) == calls_before


def test_empty_registration_does_not_invoke_factory(
    registry: EventRegistry, default_factory: CountingDefaultFactory
) -> None:
    handlers: ImmutableList[BaseEventHandler[EventA, FakeHandleResult]] = ImmutableList([])

    registry[EventA] = handlers

    assert registry[EventA] is handlers
    assert list(registry[EventA]) == []
    assert default_factory.produced == []
