from typing import Dict
from googleapiclient.errors import HttpError

LABEL_IMPORTANT = 'Classifier/Important'
LABEL_OPTIONAL = 'Classifier/Optional'

def get_label_id(service, label_name: str, userId: str = 'me') -> str | None:
    """Get label ID by name, return None if not found."""
    try:
        results = service.users().labels().list(userId=userId).execute()
        labels = results.get('labels', [])

        for label in labels:
            if label['name'] == label_name:
                return label['id']

        return None
    except HttpError as error:
        print(f"An error occurred while listing labels: {error}")
        return None

def create_label(service, label_name: str, userId: str = 'me') -> str:
    """Create a new label and return its ID."""
    label_object = {
        'name': label_name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }

    try:
        result = service.users().labels().create(
            userId=userId,
            body=label_object
        ).execute()

        return result['id']
    except HttpError as error:
        print(f"An error occurred while creating label '{label_name}': {error}")
        raise

def ensure_labels_exist(service, userId: str = 'me') -> Dict[str, str]:
    """Ensure required labels exist, create if missing.

    Returns:
        Dict mapping 'important' and 'optional' to label IDs
    """
    label_ids = {}

    try:
        for key, label_name in [('important', LABEL_IMPORTANT),
                                ('optional', LABEL_OPTIONAL)]:
            label_id = get_label_id(service, label_name, userId)
            if label_id is None:
                label_id = create_label(service, label_name, userId)
            label_ids[key] = label_id

        return label_ids
    except HttpError as error:
        print(f"An error occurred while ensuring labels exist: {error}")
        raise
