import os
import sys
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.modify']


class AuthenticationError(Exception):
    """Raised when Gmail OAuth token is revoked and cannot be refreshed headlessly."""
    pass


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    token_path = Path.home() / '.inbox-classifier' / 'token.json'
    # Use path relative to this module's location (project root)
    module_dir = Path(__file__).parent.parent
    creds_path = module_dir / 'credentials.json'

    # Create config directory if needed
    token_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing token
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError as e:
                raise AuthenticationError(
                    f"Gmail OAuth refresh token revoked or expired: {e}\n"
                    "Re-authenticate on a machine with a browser:\n"
                    "  1. Run inbox-classifier locally (Mac)\n"
                    "  2. Copy ~/.inbox-classifier/token.json to Linux"
                ) from e

        if not creds:
            if not creds_path.exists():
                raise FileNotFoundError(
                    "credentials.json not found. "
                    "Download from Google Cloud Console."
                )
            # Only attempt browser auth if DISPLAY is available (not headless)
            if not os.environ.get('DISPLAY') and not sys.stdout.isatty():
                raise AuthenticationError(
                    "No valid token and no browser available (headless server).\n"
                    "Re-authenticate on a machine with a browser:\n"
                    "  1. Run inbox-classifier locally (Mac)\n"
                    "  2. Copy ~/.inbox-classifier/token.json to Linux"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)
