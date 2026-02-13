import os
import time
import logging
from dotenv import load_dotenv

from .gmail_auth import get_gmail_service
from .gmail_labels import ensure_labels_exist, get_label_names
from .email_fetcher import fetch_unread_emails, get_email_details
from .ai_classifier import classify_email, load_rules, parse_categories
from .email_labeler import apply_label
from .logger import ClassificationLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_emails():
    """Process unread emails: fetch, classify, label."""
    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")

    # Parse categories from rules
    rules = load_rules()
    categories = parse_categories(rules)

    # Initialize components
    service = get_gmail_service()
    label_ids = ensure_labels_exist(service, categories)
    classification_logger = ClassificationLogger()

    # Fetch unread emails (exclude already classified)
    exclude_labels = get_label_names(categories)
    messages = fetch_unread_emails(service, exclude_labels=exclude_labels)

    if not messages:
        logger.info("No new emails to process")
        return

    logger.info(f"Processing {len(messages)} unread emails")

    # Process each email
    for msg in messages:
        try:
            # Get email details
            email = get_email_details(service, msg['id'])

            # Classify with AI
            result = classify_email(email, api_key)

            # Apply the matching label
            label_id = label_ids[result['classification']]
            apply_label(service, email['id'], label_id)

            # Log the classification
            classification_logger.log_classification(
                email_id=email['id'],
                subject=email['subject'],
                sender=email['sender'],
                classification=result['classification'],
                reasoning=result['reasoning']
            )

            logger.info(
                f"Classified '{email['subject'][:50]}...' as "
                f"{result['classification']}: {result['reasoning']}"
            )

        except Exception as e:
            logger.error(f"Error processing email {msg['id']}: {e}")
            continue

def main():
    """Main service loop."""
    logger.info("Starting inbox classifier service")

    while True:
        try:
            process_emails()
            logger.info("Waiting 60 seconds before next check...")
            time.sleep(60)

        except KeyboardInterrupt:
            logger.info("Service stopped by user")
            break

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            logger.info("Retrying in 5 minutes...")
            time.sleep(300)

if __name__ == '__main__':
    main()
