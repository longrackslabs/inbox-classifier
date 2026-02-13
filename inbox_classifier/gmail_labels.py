from typing import Dict, List
from googleapiclient.errors import HttpError

LABEL_PREFIX = 'Classifier'


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

def ensure_labels_exist(service, categories: List[str], userId: str = 'me') -> Dict[str, str]:
    """Ensure Gmail labels exist for all categories, create if missing.

    Args:
        service: Gmail API service
        categories: List of category names (e.g. ['IMPORTANT', 'ROUTINE', 'OPTIONAL'])

    Returns:
        Dict mapping lowercase category name to label ID
    """
    label_ids = {}

    try:
        for category in categories:
            label_name = f'{LABEL_PREFIX}/{category}'
            label_id = get_label_id(service, label_name, userId)
            if label_id is None:
                label_id = create_label(service, label_name, userId)
            label_ids[category] = label_id

        return label_ids
    except HttpError as error:
        print(f"An error occurred while ensuring labels exist: {error}")
        raise


def get_label_names(categories: List[str]) -> List[str]:
    """Get Gmail label names for all categories."""
    return [f'{LABEL_PREFIX}/{c}' for c in categories]
