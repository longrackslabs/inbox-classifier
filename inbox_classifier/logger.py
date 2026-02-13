import json
from pathlib import Path
from datetime import datetime
from typing import Union

class ClassificationLogger:
    """Logger for email classifications."""

    def __init__(self, log_path: Union[str, Path] = None):
        """Initialize logger.

        Args:
            log_path: Path to JSONL log file. Defaults to ~/.inbox-classifier/classifications.jsonl
        """
        if log_path is None:
            log_path = Path.home() / '.inbox-classifier' / 'classifications.jsonl'

        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_classification(
        self,
        email_id: str,
        subject: str,
        sender: str,
        to: str,
        classification: str,
        reasoning: str
    ):
        """Log a classification decision.

        Args:
            email_id: Gmail message ID
            subject: Email subject
            sender: Email sender
            to: Email recipient
            classification: IMPORTANT or OPTIONAL
            reasoning: Classification reasoning from AI
        """
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'email_id': email_id,
            'subject': subject,
            'sender': sender,
            'to': to,
            'classification': classification,
            'reasoning': reasoning
        }

        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
