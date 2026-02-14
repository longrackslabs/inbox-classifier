import re
from typing import List, Dict, Tuple


def parse_skip_rules(rules: str) -> List[Tuple[str, str]]:
    """Parse skip rules from rules text.

    Looks for a 'Skip classification for:' section and extracts
    from: and subject: patterns.

    Returns:
        List of (field, pattern) tuples, e.g. [('from', 'ebay@ebay.com')]
    """
    skip_patterns = []
    in_skip_section = False

    for line in rules.splitlines():
        stripped = line.strip()

        if stripped.lower() == 'skip classification for:':
            in_skip_section = True
            continue

        if in_skip_section:
            if re.match(r'^\w+ emails include:', stripped):
                break

            if stripped.startswith('- '):
                rule_text = stripped[2:].strip()
                if ':' in rule_text:
                    field, _, value = rule_text.partition(':')
                    field = field.strip().lower()
                    value = value.strip()
                    if field in ('from', 'subject') and value:
                        skip_patterns.append((field, value))

    return skip_patterns


def should_skip_email(email: Dict[str, str], skip_rules: List[Tuple[str, str]]) -> bool:
    """Check if an email matches any skip rule.

    Returns True if the email should NOT be classified.
    """
    if not skip_rules:
        return False

    for field, pattern in skip_rules:
        if field == 'from' and pattern.lower() in email['sender'].lower():
            return True
        if field == 'subject' and pattern.lower() in email['subject'].lower():
            return True

    return False
