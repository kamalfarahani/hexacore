import uuid

import pytest


@pytest.fixture
def unique_name() -> str:
    """Return a unique short identifier for queues/exchanges."""
    return f"test-{uuid.uuid4().hex[:12]}"
