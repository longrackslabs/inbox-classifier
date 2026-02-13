from unittest.mock import Mock, MagicMock
from inbox_classifier.gmail_labels import ensure_labels_exist, get_label_id

def test_ensure_labels_exist_creates_missing_labels():
    """Test that missing labels are created."""
    mock_service = MagicMock()

    # Mock the list call to return no labels
    mock_list = MagicMock()
    mock_list.execute.return_value = {'labels': []}

    # Mock the create call to return different IDs for each label
    mock_create = MagicMock()
    create_returns = [
        {'id': 'Label_123', 'name': 'Classifier/Important'},
        {'id': 'Label_456', 'name': 'Classifier/Optional'}
    ]
    mock_create.execute.side_effect = create_returns

    # Set up the mock chain
    mock_labels = MagicMock()
    mock_labels.list.return_value = mock_list
    mock_labels.create.return_value = mock_create

    mock_users = MagicMock()
    mock_users.labels.return_value = mock_labels

    mock_service.users.return_value = mock_users

    label_ids = ensure_labels_exist(mock_service)

    assert 'important' in label_ids
    assert 'optional' in label_ids
    assert label_ids['important'] == 'Label_123'
    assert label_ids['optional'] == 'Label_456'
    assert mock_labels.create.call_count == 2

def test_get_label_id_returns_existing_label():
    """Test getting ID of existing label."""
    mock_service = Mock()
    mock_service.users().labels().list().execute.return_value = {
        'labels': [
            {'id': 'Label_123', 'name': 'Classifier/Important'},
            {'id': 'Label_456', 'name': 'Classifier/Optional'}
        ]
    }

    label_id = get_label_id(mock_service, 'Classifier/Important')

    assert label_id == 'Label_123'
