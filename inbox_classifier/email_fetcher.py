import base64
from typing import List, Dict

def fetch_unread_emails(service, label_ids: List[str] = None) -> List[Dict]:
    """Fetch unread emails from inbox, optionally excluding labeled ones.

    Args:
        service: Gmail API service
        label_ids: List of label IDs to exclude (already classified emails)

    Returns:
        List of message objects with 'id' field
    """
    query = 'is:unread in:inbox'

    # Exclude already classified emails
    if label_ids:
        for label_id in label_ids:
            query += f' -label:{label_id}'

    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=100
    ).execute()

    return results.get('messages', [])

def get_email_details(service, message_id: str) -> Dict[str, str]:
    """Get email subject, sender, and body preview.

    Returns:
        Dict with keys: id, subject, sender, body, label_ids
    """
    message = service.users().messages().get(
        userId='me',
        id=message_id,
        format='full'
    ).execute()

    headers = message['payload'].get('headers', [])
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), '')

    # Extract body (handle both body.data and parts)
    body = ''
    payload = message['payload']

    if 'body' in payload and 'data' in payload['body']:
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    elif 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                break

    # Limit body to first 300 characters
    body_preview = body[:300] if body else ''

    return {
        'id': message_id,
        'subject': subject,
        'sender': sender,
        'body': body_preview,
        'label_ids': message.get('labelIds', [])
    }
