"""Unit tests for chat spam content filtering.

Scope:
- Block obvious phishing and spam-shaped payloads.
- Allow common legitimate chat content (single URLs, contact emails, markdown links).
"""

from app.modules.chat.content_filter import SpamContentFilter


class TestSpamContentFilter:
    """Behavioral checks for spam content classification."""

    def test_blocks_known_phishing_domain(self) -> None:
        """Messages containing known phishing domains are rejected."""
        content_filter = SpamContentFilter()

        result = content_filter.evaluate(
            "Please visit https://spam.ru/login to verify your account"
        )

        assert result.allowed is False
        assert result.reason == "phishing_domain_detected"

    def test_blocks_known_phishing_domain_with_port(self) -> None:
        """Port-qualified phishing URLs are still blocked by hostname matching."""
        content_filter = SpamContentFilter()

        result = content_filter.evaluate(
            "Please visit https://spam.ru:443/login to verify your account"
        )

        assert result.allowed is False
        assert result.reason == "phishing_domain_detected"

    def test_blocks_repeated_same_url_pattern(self) -> None:
        """Repeated same-domain URLs above threshold are treated as spam."""
        content_filter = SpamContentFilter(repeated_same_url_threshold=3)

        result = content_filter.evaluate(
            "https://example.org/a https://example.org/b "
            "https://example.org/c https://example.org/d"
        )

        assert result.allowed is False
        assert result.reason == "repeated_url_pattern"

    def test_blocks_shortener_abuse(self) -> None:
        """Excessive URL shorteners in one message are blocked."""
        content_filter = SpamContentFilter(shortener_abuse_threshold=2)

        result = content_filter.evaluate("https://bit.ly/1 https://tinyurl.com/2 https://bit.ly/3")

        assert result.allowed is False
        assert result.reason == "shortener_abuse"

    def test_blocks_excessive_all_caps_message(self) -> None:
        """Long all-caps content is blocked as likely spam."""
        content_filter = SpamContentFilter(caps_min_length=20, caps_ratio_threshold=0.7)

        result = content_filter.evaluate(
            "THIS IS A LIMITED OFFER ACT NOW CLICK IMMEDIATELY FOR FREE ACCESS"
        )

        assert result.allowed is False
        assert result.reason == "all_caps_spam"

    def test_allows_legitimate_single_url(self) -> None:
        """A normal single URL in message context remains allowed."""
        content_filter = SpamContentFilter()

        result = content_filter.evaluate("Check this tutorial: https://example.com/docs")

        assert result.allowed is True
        assert result.reason is None

    def test_allows_contextual_email_text(self) -> None:
        """Normal contact email usage remains allowed."""
        content_filter = SpamContentFilter()

        result = content_filter.evaluate("Contact me at user@example.com for details")

        assert result.allowed is True
        assert result.reason is None
