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
