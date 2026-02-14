from unittest.mock import Mock
from inbox_classifier.email_labeler import apply_label

def test_apply_label_adds_label_to_message():
    """Test applying label to email and archiving."""
    mock_service = Mock()
    mock_service.users().messages().modify().execute.return_value = {
        'id': 'msg1',
        'labelIds': ['Label_123']
    }

    result = apply_label(mock_service, 'msg1', 'Label_123')

    assert result['id'] == 'msg1'
    mock_service.users().messages().modify.assert_called_with(
        userId='me',
        id='msg1',
        body={
            'addLabelIds': ['Label_123'],
            'removeLabelIds': ['INBOX']
        }
    )
