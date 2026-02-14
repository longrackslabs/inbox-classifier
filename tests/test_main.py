import pytest
from unittest.mock import Mock, patch, call
from inbox_classifier.main import process_emails

@patch('inbox_classifier.main.load_dotenv')
@patch('inbox_classifier.main.os.getenv')
@patch('inbox_classifier.main.load_rules')
@patch('inbox_classifier.main.parse_categories')
@patch('inbox_classifier.main.get_gmail_service')
@patch('inbox_classifier.main.ensure_labels_exist')
@patch('inbox_classifier.main.get_label_names')
@patch('inbox_classifier.main.fetch_unread_emails')
@patch('inbox_classifier.main.get_email_details')
@patch('inbox_classifier.main.classify_email')
@patch('inbox_classifier.main.apply_label')
@patch('inbox_classifier.main.ClassificationLogger')
def test_process_emails_full_workflow(
    mock_logger_class,
    mock_apply_label,
    mock_classify,
    mock_get_details,
    mock_fetch,
    mock_get_label_names,
    mock_ensure_labels,
    mock_get_service,
    mock_parse_categories,
    mock_load_rules,
    mock_getenv,
    mock_load_dotenv
):
    """Test the complete email processing workflow."""
    # Setup mocks
    mock_getenv.return_value = 'test-api-key'
    mock_load_rules.return_value = 'Important emails include:\n- stuff\n\nRoutine emails include:\n- stuff\n\nOptional emails include:\n- stuff'
    mock_parse_categories.return_value = ['Important', 'Routine', 'Optional']
    mock_service = Mock()
    mock_get_service.return_value = mock_service

    mock_label_ids = {'Important': 'label-123', 'Routine': 'label-789', 'Optional': 'label-456'}
    mock_ensure_labels.return_value = mock_label_ids
    mock_get_label_names.return_value = ['Important', 'Routine', 'Optional']

    # Mock email data
    mock_fetch.return_value = [
        {'id': 'msg-1'},
        {'id': 'msg-2'}
    ]

    mock_get_details.side_effect = [
        {
            'id': 'msg-1',
            'subject': 'Important Email',
            'sender': 'boss@work.com',
            'to': 'me@example.com',
            'body': 'Urgent meeting'
        },
        {
            'id': 'msg-2',
            'subject': 'Newsletter',
            'sender': 'news@company.com',
            'to': 'me@example.com',
            'body': 'Weekly update'
        }
    ]

    mock_classify.side_effect = [
        {'classification': 'Important', 'reasoning': 'Work email'},
        {'classification': 'Optional', 'reasoning': 'Newsletter'}
    ]

    mock_logger = Mock()
    mock_logger_class.return_value = mock_logger

    # Run
    process_emails()

    # Verify workflow
    mock_load_dotenv.assert_called_once()
    mock_getenv.assert_called_once_with('ANTHROPIC_API_KEY')
    mock_load_rules.assert_called_once()
    mock_parse_categories.assert_called_once()
    mock_get_service.assert_called_once()
    mock_ensure_labels.assert_called_once_with(mock_service, ['Important', 'Routine', 'Optional'])
    mock_get_label_names.assert_called_once_with(['Important', 'Routine', 'Optional'])

    mock_fetch.assert_called_once_with(
        mock_service,
        exclude_labels=['Important', 'Routine', 'Optional']
    )

    # Verify both emails were processed
    assert mock_get_details.call_count == 2
    assert mock_classify.call_count == 2

    # Verify correct labels applied
    mock_apply_label.assert_has_calls([
        call(mock_service, 'msg-1', 'label-123'),  # Important
        call(mock_service, 'msg-2', 'label-456')   # Optional
    ])

    # Verify logging
    assert mock_logger.log_classification.call_count == 2
    mock_logger.log_classification.assert_any_call(
        email_id='msg-1',
        subject='Important Email',
        sender='boss@work.com',
        to='me@example.com',
        classification='Important',
        reasoning='Work email'
    )

@patch('inbox_classifier.main.load_dotenv')
@patch('inbox_classifier.main.os.getenv')
def test_process_emails_missing_api_key(mock_getenv, mock_load_dotenv):
    """Test that missing API key raises error."""
    mock_getenv.return_value = None

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
        process_emails()

@patch('inbox_classifier.main.load_dotenv')
@patch('inbox_classifier.main.os.getenv')
@patch('inbox_classifier.main.load_rules')
@patch('inbox_classifier.main.parse_categories')
@patch('inbox_classifier.main.get_gmail_service')
@patch('inbox_classifier.main.ensure_labels_exist')
@patch('inbox_classifier.main.get_label_names')
@patch('inbox_classifier.main.fetch_unread_emails')
@patch('inbox_classifier.main.ClassificationLogger')
def test_process_emails_no_messages(
    mock_logger_class,
    mock_fetch,
    mock_get_label_names,
    mock_ensure_labels,
    mock_get_service,
    mock_parse_categories,
    mock_load_rules,
    mock_getenv,
    mock_load_dotenv
):
    """Test handling when no emails to process."""
    mock_getenv.return_value = 'test-api-key'
    mock_load_rules.return_value = 'Important emails include:\n- stuff'
    mock_parse_categories.return_value = ['Important', 'Routine', 'Optional']
    mock_service = Mock()
    mock_get_service.return_value = mock_service
    mock_ensure_labels.return_value = {'Important': 'label-123', 'Routine': 'label-789', 'Optional': 'label-456'}
    mock_get_label_names.return_value = ['Important', 'Routine', 'Optional']
    mock_fetch.return_value = []

    # Should complete without error
    process_emails()

    mock_fetch.assert_called_once()

@patch('inbox_classifier.main.load_dotenv')
@patch('inbox_classifier.main.os.getenv')
@patch('inbox_classifier.main.load_rules')
@patch('inbox_classifier.main.parse_categories')
@patch('inbox_classifier.main.get_gmail_service')
@patch('inbox_classifier.main.ensure_labels_exist')
@patch('inbox_classifier.main.get_label_names')
@patch('inbox_classifier.main.fetch_unread_emails')
@patch('inbox_classifier.main.get_email_details')
@patch('inbox_classifier.main.classify_email')
@patch('inbox_classifier.main.apply_label')
@patch('inbox_classifier.main.ClassificationLogger')
def test_process_emails_error_handling(
    mock_logger_class,
    mock_apply_label,
    mock_classify,
    mock_get_details,
    mock_fetch,
    mock_get_label_names,
    mock_ensure_labels,
    mock_get_service,
    mock_parse_categories,
    mock_load_rules,
    mock_getenv,
    mock_load_dotenv
):
    """Test that errors on individual emails don't stop processing."""
    mock_getenv.return_value = 'test-api-key'
    mock_load_rules.return_value = 'Important emails include:\n- stuff'
    mock_parse_categories.return_value = ['Important', 'Routine', 'Optional']
    mock_service = Mock()
    mock_get_service.return_value = mock_service
    mock_ensure_labels.return_value = {'Important': 'label-123', 'Routine': 'label-789', 'Optional': 'label-456'}
    mock_get_label_names.return_value = ['Important', 'Routine', 'Optional']

    mock_fetch.return_value = [
        {'id': 'msg-1'},
        {'id': 'msg-2'}
    ]

    # First email fails, second succeeds
    mock_get_details.side_effect = [
        Exception("API error"),
        {
            'id': 'msg-2',
            'subject': 'Test',
            'sender': 'test@test.com',
            'to': 'me@example.com',
            'body': 'Body'
        }
    ]

    mock_classify.return_value = {'classification': 'Important', 'reasoning': 'Test'}
    mock_logger = Mock()
    mock_logger_class.return_value = mock_logger

    # Should not raise exception
    process_emails()

    # Second email should still be processed
    assert mock_classify.call_count == 1
    assert mock_apply_label.call_count == 1
