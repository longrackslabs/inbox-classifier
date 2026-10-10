from unittest.mock import Mock, patch

import pytest
import requests

from inbox_classifier.ai_classifier import classify_email

EMAIL = {'subject': 'Test receipt', 'sender': 'shop@example.com',
         'to': 'test@example.com', 'body': 'This is a synthetic test receipt.'}
KEY = 'synthetic-secret-key'


@pytest.fixture(autouse=True)
def local_rules():
    with patch('inbox_classifier.ai_classifier.load_rules', return_value='Important emails include:\n- Receipts'), patch('inbox_classifier.ai_classifier.time.sleep'):
        yield


def test_key_uses_header_and_classification_still_works():
    response = Mock()
    response.json.return_value = {'candidates': [{'content': {'parts': [{'text': 'Important: receipt'}]}}]}
    with patch('inbox_classifier.ai_classifier.requests.post', return_value=response) as post:
        assert classify_email(EMAIL, KEY)['classification'] == 'Important'
    args, kwargs = post.call_args
    assert KEY not in args[0]
    assert '?' not in args[0]
    assert kwargs['headers'] == {'x-goog-api-key': KEY}


@pytest.mark.parametrize('status', [401, 429, 503])
def test_http_error_never_exposes_credentials(status):
    response = requests.Response()
    response.status_code = status
    response.url = 'https://example.com/?key=' + KEY
    with patch('inbox_classifier.ai_classifier.requests.post', return_value=response):
        with pytest.raises(RuntimeError) as caught:
            classify_email(EMAIL, KEY)
    assert str(caught.value) == f'Gemini request failed (HTTP {status})'
    assert KEY not in str(caught.value)
    assert caught.value.__suppress_context__


def test_connection_error_never_exposes_credentials():
    with patch('inbox_classifier.ai_classifier.requests.post', side_effect=requests.ConnectionError('url?key=' + KEY)):
        with pytest.raises(RuntimeError) as caught:
            classify_email(EMAIL, KEY)
    assert str(caught.value) == 'Gemini request failed (ConnectionError)'
    assert KEY not in str(caught.value)
