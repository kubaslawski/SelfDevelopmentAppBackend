"""
Pytest configuration for the project.
"""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Return a DRF API client."""
    return APIClient()


@pytest.fixture(scope="session")
def django_db_setup():
    """Configure Django DB for pytest."""
    pass

