import json
from pathlib import Path
from inbox_classifier.logger import ClassificationLogger

def test_logger_writes_to_file(tmp_path):
    """Test that logger writes classifications to JSONL."""
    log_file = tmp_path / "test.jsonl"
    logger = ClassificationLogger(log_file)

    logger.log_classification(
        email_id='msg1',
        subject='Test Subject',
        sender='test@example.com',
        to='me@example.com',
        classification='Important',
        reasoning='Test reason'
    )

    assert log_file.exists()

    with open(log_file) as f:
        line = f.readline()
        entry = json.loads(line)

        assert entry['email_id'] == 'msg1'
        assert entry['classification'] == 'Important'
        assert entry['to'] == 'me@example.com'
        assert 'timestamp' in entry

def test_logger_creates_directory(tmp_path):
    """Test that logger creates parent directory."""
    log_file = tmp_path / "subdir" / "test.jsonl"
    logger = ClassificationLogger(log_file)

    logger.log_classification(
        email_id='msg1',
        subject='Test',
        sender='test@example.com',
        to='me@example.com',
        classification='Optional',
        reasoning='Test'
    )

    assert log_file.exists()
