from inbox_classifier.skip_rules import parse_skip_rules, should_skip_email
from inbox_classifier.ai_classifier import parse_categories

RULES_WITH_SKIP = """0_Important emails include:
- Security: password resets, security alerts

1_Routine emails include:
- Monthly statements

Skip classification for:
- from:ebay@ebay.com
- from:notifications@ebay.com
- subject:Your item sold
- subject:Payment received"""

RULES_WITHOUT_SKIP = """0_Important emails include:
- Security: password resets

1_Routine emails include:
- Monthly statements"""


def test_parse_skip_rules():
    """Test parsing skip rules from rules text."""
    rules = parse_skip_rules(RULES_WITH_SKIP)

    assert len(rules) == 4
    assert ('from', 'ebay@ebay.com') in rules
    assert ('from', 'notifications@ebay.com') in rules
    assert ('subject', 'Your item sold') in rules
    assert ('subject', 'Payment received') in rules


def test_parse_skip_rules_no_skip_section():
    """Test parsing rules with no skip section returns empty list."""
    rules = parse_skip_rules(RULES_WITHOUT_SKIP)

    assert rules == []


def test_parse_skip_rules_empty_skip_section():
    """Test parsing empty skip section returns empty list."""
    rules_text = """0_Important emails include:
- stuff

Skip classification for:

1_Routine emails include:
- stuff"""
    rules = parse_skip_rules(rules_text)

    assert rules == []


def test_parse_skip_rules_multiple_from_patterns():
    """Test parsing multiple from patterns."""
    rules_text = """Skip classification for:
- from:seller1@ebay.com
- from:seller2@ebay.com
- from:billing@utility.com"""
    rules = parse_skip_rules(rules_text)

    assert len(rules) == 3
    assert all(field == 'from' for field, _ in rules)


def test_parse_skip_rules_ignores_invalid_prefixes():
    """Test that unknown field prefixes are ignored."""
    rules_text = """Skip classification for:
- from:ebay@ebay.com
- body:something
- invalid:pattern
- subject:Your item sold"""
    rules = parse_skip_rules(rules_text)

    assert len(rules) == 2
    assert ('from', 'ebay@ebay.com') in rules
    assert ('subject', 'Your item sold') in rules


def test_parse_skip_rules_strips_whitespace():
    """Test that whitespace is stripped from patterns."""
    rules_text = """Skip classification for:
- from:  ebay@ebay.com
- subject:  Your item sold  """
    rules = parse_skip_rules(rules_text)

    assert rules == [('from', 'ebay@ebay.com'), ('subject', 'Your item sold')]


def test_parse_skip_rules_handles_colons_in_value():
    """Test that colons in the value are preserved."""
    rules_text = """Skip classification for:
- subject:Re: Your item sold"""
    rules = parse_skip_rules(rules_text)

    assert rules == [('subject', 'Re: Your item sold')]


def test_should_skip_email_matches_from():
    """Test matching email by sender."""
    email = {'sender': 'eBay <ebay@ebay.com>', 'subject': 'You sold an item'}
    skip_rules = [('from', 'ebay@ebay.com')]

    assert should_skip_email(email, skip_rules) is True


def test_should_skip_email_matches_subject():
    """Test matching email by subject."""
    email = {'sender': 'someone@example.com', 'subject': 'Your item sold - Widget'}
    skip_rules = [('subject', 'Your item sold')]

    assert should_skip_email(email, skip_rules) is True


def test_should_skip_email_case_insensitive():
    """Test that matching is case insensitive."""
    email = {'sender': 'EBAY@EBAY.COM', 'subject': 'YOUR ITEM SOLD'}
    skip_rules = [('from', 'ebay@ebay.com')]

    assert should_skip_email(email, skip_rules) is True


def test_should_skip_email_no_match():
    """Test that non-matching emails are not skipped."""
    email = {'sender': 'boss@work.com', 'subject': 'Meeting tomorrow'}
    skip_rules = [('from', 'ebay@ebay.com'), ('subject', 'Your item sold')]

    assert should_skip_email(email, skip_rules) is False


def test_should_skip_email_empty_rules():
    """Test that empty rules never skip."""
    email = {'sender': 'anyone@example.com', 'subject': 'Anything'}

    assert should_skip_email(email, []) is False


def test_should_skip_email_partial_subject_match():
    """Test substring matching on subject."""
    email = {'sender': 'ebay@ebay.com', 'subject': 'Re: Your item sold on eBay'}
    skip_rules = [('subject', 'Your item sold')]

    assert should_skip_email(email, skip_rules) is True


def test_parse_skip_rules_does_not_interfere_with_categories():
    """Test that skip section doesn't affect category parsing."""
    categories = parse_categories(RULES_WITH_SKIP)

    assert categories == ['0_Important', '1_Routine']
    assert 'Skip' not in categories


def test_skip_section_after_categories():
    """Test skip section works when placed after all categories."""
    rules_text = """0_Important emails include:
- stuff

1_Routine emails include:
- stuff

Skip classification for:
- from:test@test.com"""
    rules = parse_skip_rules(rules_text)

    assert rules == [('from', 'test@test.com')]
