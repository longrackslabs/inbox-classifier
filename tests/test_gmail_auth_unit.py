"""Unit tests for Gmail authentication with mocked dependencies."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from google.auth.exceptions import RefreshError
from inbox_classifier.gmail_auth import get_gmail_service, AuthenticationError, SCOPES


@pytest.fixture
def mock_token_path(tmp_path):
    """Create a temporary token path."""
    return tmp_path / '.inbox-classifier' / 'token.json'


@pytest.fixture
def mock_creds_path(tmp_path):
    """Create a temporary credentials path."""
    return tmp_path / 'credentials.json'


class TestGetGmailService:
    """Tests for get_gmail_service function."""

    @patch('inbox_classifier.gmail_auth.build')
    @patch('inbox_classifier.gmail_auth.Credentials')
    @patch('inbox_classifier.gmail_auth.Path')
    def test_loads_valid_token(self, mock_path_class, mock_creds_class, mock_build):
        """Test that valid existing token is loaded and used."""
        # Setup mocks
        mock_token_path = Mock()
        mock_token_path.exists.return_value = True
        mock_token_path.parent.mkdir = Mock()

        mock_creds_path = Mock()
        mock_creds_path.exists.return_value = True

        # Configure Path() calls
        mock_path_class.home.return_value = Mock(__truediv__=lambda s, x: Mock(__truediv__=lambda s, y: mock_token_path))
        mock_path_class.return_value.__truediv__ = lambda s, x: mock_creds_path
        mock_path_class.return_value.parent.parent = Mock(__truediv__=lambda s, x: mock_creds_path)

        # Mock credentials as valid
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds_class.from_authorized_user_file.return_value = mock_creds

        mock_service = Mock()
        mock_build.return_value = mock_service

        # Execute
        result = get_gmail_service()

        # Verify
        assert result == mock_service
        mock_creds_class.from_authorized_user_file.assert_called_once()
        mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)

    @patch('inbox_classifier.gmail_auth.build')
    @patch('inbox_classifier.gmail_auth.Request')
    @patch('inbox_classifier.gmail_auth.Credentials')
    @patch('inbox_classifier.gmail_auth.Path')
    @patch('builtins.open', new_callable=mock_open)
    def test_refreshes_expired_token(self, mock_file, mock_path_class, mock_creds_class, mock_request, mock_build):
        """Test that expired token is refreshed successfully."""
        # Setup mocks
        mock_token_path = Mock()
        mock_token_path.exists.return_value = True
        mock_token_path.parent.mkdir = Mock()

        mock_creds_path = Mock()

        # Configure Path() calls
        mock_path_class.home.return_value = Mock(__truediv__=lambda s, x: Mock(__truediv__=lambda s, y: mock_token_path))
        mock_path_class.return_value.__truediv__ = lambda s, x: mock_creds_path
        mock_path_class.return_value.parent.parent = Mock(__truediv__=lambda s, x: mock_creds_path)

        # Mock credentials as expired with refresh token
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = 'refresh_token'
        mock_creds.to_json.return_value = '{"token": "refreshed"}'

        # After refresh, make it valid
        def refresh_side_effect(request):
            mock_creds.valid = True

        mock_creds.refresh.side_effect = refresh_side_effect
        mock_creds_class.from_authorized_user_file.return_value = mock_creds

        mock_service = Mock()
        mock_build.return_value = mock_service

        # Execute
        result = get_gmail_service()

        # Verify
        assert result == mock_service
        mock_creds.refresh.assert_called_once()
        mock_file.assert_called_once()
        mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)

    @patch('inbox_classifier.gmail_auth.Request')
    @patch('inbox_classifier.gmail_auth.Credentials')
    @patch('inbox_classifier.gmail_auth.Path')
    def test_refresh_failure_raises_auth_error(self, mock_path_class, mock_creds_class,
                                               mock_request):
        """Test that refresh failure raises AuthenticationError (no silent browser fallback)."""
        # Setup mocks
        mock_token_path = Mock()
        mock_token_path.exists.return_value = True
        mock_token_path.parent.mkdir = Mock()

        mock_path_class.home.return_value = Mock(__truediv__=lambda s, x: Mock(__truediv__=lambda s, y: mock_token_path))

        # Mock credentials as expired with refresh token
        mock_old_creds = Mock()
        mock_old_creds.valid = False
        mock_old_creds.expired = True
        mock_old_creds.refresh_token = 'refresh_token'
        mock_old_creds.refresh.side_effect = RefreshError('Refresh failed')

        mock_creds_class.from_authorized_user_file.return_value = mock_old_creds

        # Execute — should raise AuthenticationError, not silently try browser
        with pytest.raises(AuthenticationError, match="refresh token revoked or expired"):
            get_gmail_service()

    @patch('inbox_classifier.gmail_auth.Path')
    def test_missing_credentials_error(self, mock_path_class):
        """Test that missing credentials.json raises FileNotFoundError."""
        # Setup mocks
        mock_token_path = Mock()
        mock_token_path.exists.return_value = False
        mock_token_path.parent.mkdir = Mock()

        mock_creds_path = Mock()
        mock_creds_path.exists.return_value = False

        # Configure Path() calls
        mock_path_instance = Mock()
        mock_path_instance.__truediv__ = Mock(return_value=mock_creds_path)
        mock_path_instance.parent.parent = mock_path_instance

        mock_path_class.home.return_value = Mock(__truediv__=lambda s, x: Mock(__truediv__=lambda s, y: mock_token_path))
        mock_path_class.return_value = mock_path_instance

        # Execute and verify
        with pytest.raises(FileNotFoundError, match="credentials.json not found"):
            get_gmail_service()

    @patch('inbox_classifier.gmail_auth.sys')
    @patch('inbox_classifier.gmail_auth.build')
    @patch('inbox_classifier.gmail_auth.InstalledAppFlow')
    @patch('inbox_classifier.gmail_auth.Path')
    @patch('builtins.open', new_callable=mock_open)
    def test_creates_token_directory(self, mock_file, mock_path_class, mock_flow_class, mock_build, mock_sys):
        """Test that token directory is created if it doesn't exist."""
        mock_sys.stdout.isatty.return_value = True
        # Setup mocks
        mock_token_path = Mock()
        mock_token_path.exists.return_value = False
        mock_token_path.parent = Mock()

        mock_creds_path = Mock()
        mock_creds_path.exists.return_value = True

        # Configure Path() calls
        mock_path_instance = Mock()
        mock_path_instance.__truediv__ = Mock(return_value=mock_creds_path)
        mock_path_instance.parent.parent = mock_path_instance

        mock_path_class.home.return_value = Mock(__truediv__=lambda s, x: Mock(__truediv__=lambda s, y: mock_token_path))
        mock_path_class.return_value = mock_path_instance

        # Mock flow for authentication
        mock_flow = Mock()
        mock_creds = Mock()
        mock_creds.to_json.return_value = '{"token": "new"}'
        mock_flow.run_local_server.return_value = mock_creds
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        mock_service = Mock()
        mock_build.return_value = mock_service

        # Execute
        result = get_gmail_service()

        # Verify
        mock_token_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        assert result == mock_service

    @patch('inbox_classifier.gmail_auth.sys')
    @patch('inbox_classifier.gmail_auth.build')
    @patch('inbox_classifier.gmail_auth.InstalledAppFlow')
    @patch('inbox_classifier.gmail_auth.Path')
    @patch('builtins.open', new_callable=mock_open)
    def test_new_authentication_flow(self, mock_file, mock_path_class, mock_flow_class, mock_build, mock_sys):
        """Test complete authentication flow for new user."""
        mock_sys.stdout.isatty.return_value = True
        # Setup mocks
        mock_token_path = Mock()
        mock_token_path.exists.return_value = False
        mock_token_path.parent.mkdir = Mock()

        mock_creds_path = Mock()
        mock_creds_path.exists.return_value = True

        # Configure Path() calls
        mock_path_instance = Mock()
        mock_path_instance.__truediv__ = Mock(return_value=mock_creds_path)
        mock_path_instance.parent.parent = mock_path_instance

        mock_path_class.home.return_value = Mock(__truediv__=lambda s, x: Mock(__truediv__=lambda s, y: mock_token_path))
        mock_path_class.return_value = mock_path_instance

        # Mock flow
        mock_flow = Mock()
        mock_creds = Mock()
        mock_creds.to_json.return_value = '{"token": "abc123"}'
        mock_flow.run_local_server.return_value = mock_creds
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        mock_service = Mock()
        mock_build.return_value = mock_service

        # Execute
        result = get_gmail_service()

        # Verify
        assert result == mock_service
        mock_flow_class.from_client_secrets_file.assert_called_once()
        mock_flow.run_local_server.assert_called_once_with(port=0)
        mock_file.assert_called_once()
        mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)
