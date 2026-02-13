from unittest.mock import Mock, patch
from inbox_classifier.ai_classifier import classify_email, load_rules, parse_categories

MOCK_RULES = """IMPORTANT emails include:
- Transactional: receipts, confirmations, invoices, shipping notifications
- Security: password resets, security alerts, 2FA codes

ROUTINE emails include:
- Monthly statements, account notifications

OPTIONAL emails include:
- Promotional: sales, deals, marketing campaigns
- Newsletters: regular updates, digests"""

@patch('inbox_classifier.ai_classifier.time.sleep')
@patch('inbox_classifier.ai_classifier.load_rules')
@patch('inbox_classifier.ai_classifier.Anthropic')
def test_classify_email_returns_important(mock_anthropic, mock_load_rules, mock_sleep):
    """Test classification of important email."""
    mock_load_rules.return_value = MOCK_RULES

    mock_client = Mock()
    mock_anthropic.return_value = mock_client

    mock_response = Mock()
    mock_response.content = [Mock(text='IMPORTANT: This is a receipt')]
    mock_client.messages.create.return_value = mock_response

    email = {
        'subject': 'Your receipt',
        'sender': 'store@example.com',
        'body': 'Thank you for your purchase'
    }

    result = classify_email(email, 'test-key')

    assert result['classification'] == 'IMPORTANT'
    assert 'receipt' in result['reasoning'].lower()

@patch('inbox_classifier.ai_classifier.time.sleep')
@patch('inbox_classifier.ai_classifier.load_rules')
@patch('inbox_classifier.ai_classifier.Anthropic')
def test_classify_email_returns_optional(mock_anthropic, mock_load_rules, mock_sleep):
    """Test classification of optional email."""
    mock_load_rules.return_value = MOCK_RULES

    mock_client = Mock()
    mock_anthropic.return_value = mock_client

    mock_response = Mock()
    mock_response.content = [Mock(text='OPTIONAL: This is a newsletter')]
    mock_client.messages.create.return_value = mock_response

    email = {
        'subject': 'Weekly digest',
        'sender': 'newsletter@example.com',
        'body': 'Here are this weeks top stories'
    }

    result = classify_email(email, 'test-key')

    assert result['classification'] == 'OPTIONAL'
    assert 'newsletter' in result['reasoning'].lower()

@patch('inbox_classifier.ai_classifier.time.sleep')
@patch('inbox_classifier.ai_classifier.load_rules')
@patch('inbox_classifier.ai_classifier.Anthropic')
def test_classify_email_returns_routine(mock_anthropic, mock_load_rules, mock_sleep):
    """Test classification of routine email."""
    mock_load_rules.return_value = MOCK_RULES

    mock_client = Mock()
    mock_anthropic.return_value = mock_client

    mock_response = Mock()
    mock_response.content = [Mock(text='ROUTINE: Monthly account statement')]
    mock_client.messages.create.return_value = mock_response

    email = {
        'subject': 'Your monthly statement',
        'sender': 'bank@example.com',
        'body': 'Your statement is ready'
    }

    result = classify_email(email, 'test-key')

    assert result['classification'] == 'ROUTINE'
    assert 'statement' in result['reasoning'].lower()

@patch('inbox_classifier.ai_classifier.time.sleep')
@patch('inbox_classifier.ai_classifier.load_rules')
@patch('inbox_classifier.ai_classifier.Anthropic')
def test_classify_email_defaults_to_first_category(mock_anthropic, mock_load_rules, mock_sleep):
    """Test that unrecognized responses default to first category."""
    mock_load_rules.return_value = MOCK_RULES

    mock_client = Mock()
    mock_anthropic.return_value = mock_client

    mock_response = Mock()
    mock_response.content = [Mock(text='I am not sure about this one')]
    mock_client.messages.create.return_value = mock_response

    email = {
        'subject': 'Ambiguous',
        'sender': 'unknown@example.com',
        'body': 'Some content'
    }

    result = classify_email(email, 'test-key')

    assert result['classification'] == 'IMPORTANT'
    assert 'defaulting' in result['reasoning'].lower()

def test_parse_categories():
    """Test parsing category names from rules text."""
    categories = parse_categories(MOCK_RULES)

    assert categories == ['IMPORTANT', 'ROUTINE', 'OPTIONAL']

def test_parse_categories_single():
    """Test parsing a single category."""
    rules = "URGENT emails include:\n- Something important"
    categories = parse_categories(rules)

    assert categories == ['URGENT']

@patch('inbox_classifier.ai_classifier.RULES_FILE')
@patch('inbox_classifier.ai_classifier.CONFIG_DIR')
def test_load_rules_creates_default(mock_config_dir, mock_rules_file):
    """Test that load_rules creates default rules when file is missing."""
    mock_rules_file.exists.return_value = False

    rules = load_rules()

    assert 'IMPORTANT emails include:' in rules
    assert 'ROUTINE emails include:' in rules
    assert 'OPTIONAL emails include:' in rules
    mock_config_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
