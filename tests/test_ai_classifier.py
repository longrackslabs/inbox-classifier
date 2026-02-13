from unittest.mock import Mock, patch
from inbox_classifier.ai_classifier import classify_email

def test_classify_email_returns_important():
    """Test classification of important email."""
    with patch('inbox_classifier.ai_classifier.Anthropic') as mock_anthropic:
        mock_client = Mock()
        mock_anthropic.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text='IMPORTANT: This is a receipt')]
        mock_client.messages.create.return_value = mock_response

        email = {
            'subject': 'Your receipt',
            'sender': 'store@example.com',
            'body': 'Thank you for your purchase'
        }

        result = classify_email(email, 'test-key')

        assert result['classification'] == 'IMPORTANT'
        assert 'receipt' in result['reasoning'].lower()

def test_classify_email_returns_optional():
    """Test classification of optional email."""
    with patch('inbox_classifier.ai_classifier.Anthropic') as mock_anthropic:
        mock_client = Mock()
        mock_anthropic.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text='OPTIONAL: This is a newsletter')]
        mock_client.messages.create.return_value = mock_response

        email = {
            'subject': 'Weekly digest',
            'sender': 'newsletter@example.com',
            'body': 'Here are this weeks top stories'
        }

        result = classify_email(email, 'test-key')

        assert result['classification'] == 'OPTIONAL'
