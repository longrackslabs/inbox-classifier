from unittest.mock import Mock, MagicMock
from googleapiclient.errors import HttpError
import pytest
from inbox_classifier.gmail_labels import ensure_labels_exist, get_label_id, create_label, get_label_names

def test_ensure_labels_exist_creates_missing_labels():
    """Test that missing labels are created."""
    mock_service = MagicMock()

    # Mock the list call to return no labels
    mock_list = MagicMock()
    mock_list.execute.return_value = {'labels': []}

    # Mock the create call to return different IDs for each label
    mock_create = MagicMock()
    create_returns = [
        {'id': 'Label_123', 'name': 'Important'},
        {'id': 'Label_789', 'name': 'Routine'},
        {'id': 'Label_456', 'name': 'Optional'}
    ]
    mock_create.execute.side_effect = create_returns

    # Set up the mock chain
    mock_labels = MagicMock()
    mock_labels.list.return_value = mock_list
    mock_labels.create.return_value = mock_create

    mock_users = MagicMock()
    mock_users.labels.return_value = mock_labels

    mock_service.users.return_value = mock_users

    label_ids = ensure_labels_exist(mock_service, ['Important', 'Routine', 'Optional'])

    assert 'Important' in label_ids
    assert 'Routine' in label_ids
    assert 'Optional' in label_ids
    assert label_ids['Important'] == 'Label_123'
    assert label_ids['Routine'] == 'Label_789'
    assert label_ids['Optional'] == 'Label_456'
    assert mock_labels.create.call_count == 3

def test_get_label_id_returns_existing_label():
    """Test getting ID of existing label."""
    mock_service = Mock()
    mock_service.users().labels().list().execute.return_value = {
        'labels': [
            {'id': 'Label_123', 'name': 'Important'},
            {'id': 'Label_456', 'name': 'Optional'}
        ]
    }

    label_id = get_label_id(mock_service, 'Important')

    assert label_id == 'Label_123'

def test_ensure_labels_exist_when_labels_already_exist():
    """Test that no labels are created when they already exist."""
    mock_service = MagicMock()

    # Mock the list call to return all labels already existing
    mock_list = MagicMock()
    mock_list.execute.return_value = {
        'labels': [
            {'id': 'Label_123', 'name': 'Important'},
            {'id': 'Label_789', 'name': 'Routine'},
            {'id': 'Label_456', 'name': 'Optional'}
        ]
    }

    # Set up the mock chain
    mock_labels = MagicMock()
    mock_labels.list.return_value = mock_list

    mock_users = MagicMock()
    mock_users.labels.return_value = mock_labels

    mock_service.users.return_value = mock_users

    label_ids = ensure_labels_exist(mock_service, ['Important', 'Routine', 'Optional'])

    assert label_ids['Important'] == 'Label_123'
    assert label_ids['Routine'] == 'Label_789'
    assert label_ids['Optional'] == 'Label_456'
    # Verify create was never called
    assert mock_labels.create.call_count == 0

def test_get_label_id_when_label_not_found():
    """Test that get_label_id returns None when label is not found."""
    mock_service = Mock()
    mock_service.users().labels().list().execute.return_value = {
        'labels': [
            {'id': 'Label_123', 'name': 'Important'}
        ]
    }

    label_id = get_label_id(mock_service, 'NonExistent')

    assert label_id is None

def test_ensure_labels_exist_mixed_scenario():
    """Test mixed scenario where some labels exist and some don't."""
    mock_service = MagicMock()

    # Mock the list call to return only the Important label
    mock_list = MagicMock()
    mock_list.execute.return_value = {
        'labels': [
            {'id': 'Label_123', 'name': 'Important'}
        ]
    }

    # Mock the create call to return IDs for missing labels
    mock_create = MagicMock()
    mock_create.execute.side_effect = [
        {'id': 'Label_789', 'name': 'Routine'},
        {'id': 'Label_456', 'name': 'Optional'}
    ]

    # Set up the mock chain
    mock_labels = MagicMock()
    mock_labels.list.return_value = mock_list
    mock_labels.create.return_value = mock_create

    mock_users = MagicMock()
    mock_users.labels.return_value = mock_labels

    mock_service.users.return_value = mock_users

    label_ids = ensure_labels_exist(mock_service, ['Important', 'Routine', 'Optional'])

    assert label_ids['Important'] == 'Label_123'
    assert label_ids['Routine'] == 'Label_789'
    assert label_ids['Optional'] == 'Label_456'
    # Verify create was called twice (for Routine and Optional)
    assert mock_labels.create.call_count == 2

def test_get_label_id_handles_api_error():
    """Test that get_label_id handles HttpError gracefully."""
    mock_service = Mock()
    mock_error = HttpError(resp=Mock(status=500), content=b'Server Error')
    mock_service.users().labels().list().execute.side_effect = mock_error

    label_id = get_label_id(mock_service, 'Important')

    assert label_id is None

def test_create_label_raises_on_api_error():
    """Test that create_label raises HttpError when API call fails."""
    mock_service = MagicMock()
    mock_error = HttpError(resp=Mock(status=400), content=b'Bad Request')

    mock_create = MagicMock()
    mock_create.execute.side_effect = mock_error

    mock_labels = MagicMock()
    mock_labels.create.return_value = mock_create

    mock_users = MagicMock()
    mock_users.labels.return_value = mock_labels

    mock_service.users.return_value = mock_users

    with pytest.raises(HttpError):
        create_label(mock_service, 'TestLabel')

def test_ensure_labels_exist_raises_on_create_error():
    """Test that ensure_labels_exist raises HttpError when label creation fails."""
    mock_service = MagicMock()

    # Mock the list call to return no labels
    mock_list = MagicMock()
    mock_list.execute.return_value = {'labels': []}

    # Mock the create call to raise an error
    mock_create = MagicMock()
    mock_error = HttpError(resp=Mock(status=403), content=b'Permission Denied')
    mock_create.execute.side_effect = mock_error

    # Set up the mock chain
    mock_labels = MagicMock()
    mock_labels.list.return_value = mock_list
    mock_labels.create.return_value = mock_create

    mock_users = MagicMock()
    mock_users.labels.return_value = mock_labels

    mock_service.users.return_value = mock_users

    with pytest.raises(HttpError):
        ensure_labels_exist(mock_service, ['Important', 'Routine', 'Optional'])

def test_get_label_names():
    """Test generating label names from categories."""
    names = get_label_names(['Important', 'Routine', 'Optional'])

    assert names == ['Important', 'Routine', 'Optional']
