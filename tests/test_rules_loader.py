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
