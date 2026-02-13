import os
from pathlib import Path
from inbox_classifier.gmail_auth import get_gmail_service

def test_gmail_auth_creates_service():
    """Test that Gmail service is created successfully."""
    # This test requires valid credentials
    # Skip in CI, run manually for validation
    if not os.path.exists("credentials.json"):
        import pytest
        pytest.skip("credentials.json not found")

    service = get_gmail_service()
    assert service is not None
    assert hasattr(service, 'users')
