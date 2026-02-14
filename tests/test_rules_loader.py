import requests
from unittest.mock import patch, MagicMock
from inbox_classifier.rules_loader import load_rules

MOCK_RULES = """0_Important emails include:
- Security: password resets
- Personal: real people

1_Routine emails include:
- Monthly statements"""


@patch('inbox_classifier.rules_loader.os.getenv')
@patch('inbox_classifier.rules_loader.RULES_FILE')
def test_load_rules_local_file(mock_rules_file, mock_getenv):
    """When RULES_REPO not set, reads from local file."""
    mock_getenv.return_value = None  # no RULES_REPO
    mock_rules_file.exists.return_value = True
    mock_rules_file.read_text.return_value = MOCK_RULES

    result = load_rules()

    assert result == MOCK_RULES.strip()
    mock_rules_file.read_text.assert_called_once()


@patch('inbox_classifier.rules_loader.os.getenv')
@patch('inbox_classifier.rules_loader.RULES_FILE')
@patch('inbox_classifier.rules_loader.CONFIG_DIR')
def test_load_rules_creates_default_when_missing(mock_config_dir, mock_rules_file, mock_getenv):
    """When no RULES_REPO and no local file, creates default."""
    mock_getenv.return_value = None
    mock_rules_file.exists.return_value = False

    result = load_rules()

    assert 'Important emails include:' in result
    mock_config_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_rules_file.write_text.assert_called_once()


@patch('inbox_classifier.rules_loader.os.getenv')
@patch('inbox_classifier.rules_loader.requests.get')
@patch('inbox_classifier.rules_loader.RULES_FILE')
@patch('inbox_classifier.rules_loader.CONFIG_DIR')
def test_load_rules_fetches_from_github(mock_config_dir, mock_rules_file, mock_get, mock_getenv):
    """When RULES_REPO is set, fetches from GitHub API."""
    mock_getenv.side_effect = lambda key: {
        'RULES_REPO': 'longrackslabs/inbox-rules',
        'GITHUB_TOKEN': 'ghp_test123',
    }.get(key)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = MOCK_RULES
    mock_get.return_value = mock_response

    result = load_rules()

    assert result == MOCK_RULES
    mock_get.assert_called_once()
    call_args = mock_get.call_args
    assert 'longrackslabs/inbox-rules' in call_args[0][0]
    assert 'Authorization' in call_args[1]['headers']


@patch('inbox_classifier.rules_loader.os.getenv')
@patch('inbox_classifier.rules_loader.requests.get')
@patch('inbox_classifier.rules_loader.RULES_FILE')
@patch('inbox_classifier.rules_loader.CONFIG_DIR')
def test_load_rules_github_updates_cache(mock_config_dir, mock_rules_file, mock_get, mock_getenv):
    """Successful GitHub fetch updates local cache."""
    mock_getenv.side_effect = lambda key: {
        'RULES_REPO': 'longrackslabs/inbox-rules',
        'GITHUB_TOKEN': 'ghp_test123',
    }.get(key)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = MOCK_RULES
    mock_get.return_value = mock_response
    mock_rules_file.exists.return_value = True

    load_rules()

    mock_rules_file.write_text.assert_called_once_with(MOCK_RULES)


@patch('inbox_classifier.rules_loader.os.getenv')
@patch('inbox_classifier.rules_loader.requests.get')
@patch('inbox_classifier.rules_loader.RULES_FILE')
def test_load_rules_github_failure_uses_cache(mock_rules_file, mock_get, mock_getenv):
    """When GitHub fetch fails, falls back to local cache."""
    mock_getenv.side_effect = lambda key: {
        'RULES_REPO': 'longrackslabs/inbox-rules',
        'GITHUB_TOKEN': 'ghp_test123',
    }.get(key)

    mock_get.side_effect = requests.RequestException("Connection failed")
    mock_rules_file.exists.return_value = True
    mock_rules_file.read_text.return_value = MOCK_RULES

    result = load_rules()

    assert result == MOCK_RULES.strip()
    mock_rules_file.read_text.assert_called_once()


@patch('inbox_classifier.rules_loader.os.getenv')
@patch('inbox_classifier.rules_loader.requests.get')
@patch('inbox_classifier.rules_loader.RULES_FILE')
def test_load_rules_github_non_200_uses_cache(mock_rules_file, mock_get, mock_getenv):
    """When GitHub returns non-200, falls back to local cache."""
    mock_getenv.side_effect = lambda key: {
        'RULES_REPO': 'longrackslabs/inbox-rules',
        'GITHUB_TOKEN': 'ghp_test123',
    }.get(key)

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = 'Not Found'
    mock_get.return_value = mock_response
    mock_rules_file.exists.return_value = True
    mock_rules_file.read_text.return_value = MOCK_RULES

    result = load_rules()

    assert result == MOCK_RULES.strip()
