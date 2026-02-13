from typing import Dict

def apply_label(service, message_id: str, label_id: str) -> Dict:
    """Apply label to an email message and archive it (remove from inbox).

    Args:
        service: Gmail API service
        message_id: Email message ID
        label_id: Label ID to apply

    Returns:
        Modified message object
    """
    result = service.users().messages().modify(
        userId='me',
        id=message_id,
        body={
            'addLabelIds': [label_id],
            'removeLabelIds': ['INBOX']
        }
    ).execute()

    return result
