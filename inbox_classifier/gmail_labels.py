from typing import Dict

LABEL_IMPORTANT = 'Classifier/Important'
LABEL_OPTIONAL = 'Classifier/Optional'

def get_label_id(service, label_name: str) -> str | None:
    """Get label ID by name, return None if not found."""
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    for label in labels:
        if label['name'] == label_name:
            return label['id']

    return None

def create_label(service, label_name: str) -> str:
    """Create a new label and return its ID."""
    label_object = {
        'name': label_name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }

    result = service.users().labels().create(
        userId='me',
        body=label_object
    ).execute()

    return result['id']

def ensure_labels_exist(service) -> Dict[str, str]:
    """Ensure required labels exist, create if missing.

    Returns:
        Dict mapping 'important' and 'optional' to label IDs
    """
    label_ids = {}

    for key, label_name in [('important', LABEL_IMPORTANT),
                            ('optional', LABEL_OPTIONAL)]:
        label_id = get_label_id(service, label_name)
        if label_id is None:
            label_id = create_label(service, label_name)
        label_ids[key] = label_id

    return label_ids
