from unittest.mock import Mock, patch
from inbox_classifier.ai_classifier import classify_email, load_rules, parse_categories

MOCK_RULES = """Important emails include:
- Transactional: receipts, confirmations, invoices, shipping notifications
- Security: password resets, security alerts, 2FA codes

Routine emails include:
- Monthly statements, account notifications

Optional emails include:
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
    mock_response.content = [Mock(text='Important: This is a receipt')]
    mock_client.messages.create.return_value = mock_response

    email = {
        'subject': 'Your receipt',
        'sender': 'store@example.com',
        'to': 'me@example.com',
        'body': 'Thank you for your purchase'
    }

    result = classify_email(email, 'test-key')

    assert result['classification'] == 'Important'
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
    mock_response.content = [Mock(text='Optional: This is a newsletter')]
    mock_client.messages.create.return_value = mock_response

    email = {
        'subject': 'Weekly digest',
        'sender': 'newsletter@example.com',
        'to': 'me@example.com',
        'body': 'Here are this weeks top stories'
    }

    result = classify_email(email, 'test-key')

    assert result['classification'] == 'Optional'
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
    mock_response.content = [Mock(text='Routine: Monthly account statement')]
    mock_client.messages.create.return_value = mock_response

    email = {
        'subject': 'Your monthly statement',
        'sender': 'bank@example.com',
        'to': 'me@example.com',
        'body': 'Your statement is ready'
    }

    result = classify_email(email, 'test-key')

    assert result['classification'] == 'Routine'
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
        'to': 'me@example.com',
        'body': 'Some content'
    }

    result = classify_email(email, 'test-key')

    assert result['classification'] == 'Important'
    assert 'defaulting' in result['reasoning'].lower()

def test_parse_categories():
    """Test parsing category names from rules text."""
    categories = parse_categories(MOCK_RULES)

    assert categories == ['Important', 'Routine', 'Optional']

def test_parse_categories_single():
    """Test parsing a single category."""
    rules = "Urgent emails include:\n- Something important"
    categories = parse_categories(rules)

    assert categories == ['Urgent']

@patch('inbox_classifier.ai_classifier.RULES_FILE')
@patch('inbox_classifier.ai_classifier.CONFIG_DIR')
def test_load_rules_creates_default(mock_config_dir, mock_rules_file):
    """Test that load_rules creates default rules when file is missing."""
    mock_rules_file.exists.return_value = False

    rules = load_rules()

    assert 'Important emails include:' in rules
    assert 'Routine emails include:' in rules
    assert 'Optional emails include:' in rules
    assert 'Skip classification for:' in rules
    mock_config_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

def test_parse_categories_ignores_skip_section():
    """Test that skip classification section doesn't create a category."""
    rules = """Important emails include:
- stuff

Optional emails include:
- stuff

Skip classification for:
- from:ebay@ebay.com"""
    categories = parse_categories(rules)

    assert categories == ['Important', 'Optional']
    assert 'Skip' not in categories
