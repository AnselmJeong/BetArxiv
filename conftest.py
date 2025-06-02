import pytest
import pytest_asyncio
import os


def pytest_configure(config):
    """Register custom markers to avoid unknown marker warnings"""
    config.addinivalue_line("markers", "db: marks tests that require database connection")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    # Set test database URL if not provided
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/postgres"

    # Set test directory
    if not os.getenv("DIRECTORY"):
        os.environ["DIRECTORY"] = "docs"

    yield


# Configure pytest-asyncio to properly handle async fixtures
pytest_plugins = ("pytest_asyncio",)
