"""Unit tests for routers.py."""

from app.routers import include_routers  # noqa:E402

from app.endpoints import root, info, models, query, health, config  # noqa:E402


class MockFastAPI:
    """Mock class for FastAPI."""

    def __init__(self):
        """Initialize mock class."""
        self.routers = []

    def include_router(self, router, prefix=None):
        """Register new router."""
        self.routers.append(router)


def test_include_routers():
    """Test the function include_routers."""
    app = MockFastAPI()
    include_routers(app)

    # are all routers added?
    assert len(app.routers) == 6
    assert root.router in app.routers
    assert info.router in app.routers
    assert models.router in app.routers
    assert query.router in app.routers
    assert health.router in app.routers
    assert config.router in app.routers
