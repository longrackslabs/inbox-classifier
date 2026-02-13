import base64
from unittest.mock import Mock
from inbox_classifier.email_fetcher import fetch_unread_emails, get_email_details

def test_fetch_unread_emails_returns_message_ids():
    """Test fetching unread email IDs."""
    mock_service = Mock()
    mock_service.users().messages().list().execute.return_value = {
        'messages': [
            {'id': 'msg1'},
            {'id': 'msg2'}
        ]
    }

    messages = fetch_unread_emails(mock_service)

    assert len(messages) == 2
    assert messages[0]['id'] == 'msg1'

def test_get_email_details_extracts_metadata():
    """Test extracting email subject and sender."""
    mock_service = Mock()
    mock_service.users().messages().get().execute.return_value = {
        'id': 'msg1',
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Email'},
                {'name': 'From', 'value': 'sender@example.com'}
            ],
            'body': {
                'data': 'VGVzdCBib2R5'  # base64 for "Test body"
            }
        },
        'labelIds': ['INBOX', 'UNREAD']
    }

    details = get_email_details(mock_service, 'msg1')

    assert details['subject'] == 'Test Email'
    assert details['sender'] == 'sender@example.com'
    assert 'Test body' in details['body']

def test_fetch_unread_emails_excludes_labels():
    """Test that label exclusion works in query."""
    mock_service = Mock()
    mock_service.users().messages().list().execute.return_value = {
        'messages': []
    }

    fetch_unread_emails(mock_service, label_ids=['Label_123', 'Label_456'])

    # Verify the query includes label exclusions
    call_args = mock_service.users().messages().list.call_args
    assert '-label:Label_123' in call_args.kwargs['q']
    assert '-label:Label_456' in call_args.kwargs['q']

def test_get_email_details_handles_multipart():
    """Test extracting body from multipart messages."""
    mock_service = Mock()
    mock_service.users().messages().get().execute.return_value = {
        'id': 'msg1',
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Multipart Test'},
                {'name': 'From', 'value': 'test@example.com'}
            ],
            'parts': [
                {
                    'mimeType': 'text/plain',
                    'body': {'data': 'TXVsdGlwYXJ0IGJvZHk='}  # "Multipart body"
                }
            ]
        },
        'labelIds': ['INBOX']
    }

    details = get_email_details(mock_service, 'msg1')

    assert 'Multipart body' in details['body']

def test_get_email_details_truncates_body():
    """Test that body is truncated to 300 characters."""
    long_text = 'A' * 500
    encoded = base64.urlsafe_b64encode(long_text.encode()).decode()

    mock_service = Mock()
    mock_service.users().messages().get().execute.return_value = {
        'id': 'msg1',
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Long Email'},
                {'name': 'From', 'value': 'test@example.com'}
            ],
            'body': {'data': encoded}
        },
        'labelIds': ['INBOX']
    }

    details = get_email_details(mock_service, 'msg1')

    assert len(details['body']) == 300
    assert details['body'] == 'A' * 300
