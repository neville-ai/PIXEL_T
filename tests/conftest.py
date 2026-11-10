import sys
import os
import pytest

# Add project root and backend directory to sys.path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app import create_app
from app.core.config import TestingConfig


@pytest.fixture
def app():
    """Create application configured for testing."""
    application = create_app(TestingConfig)
    return application


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
