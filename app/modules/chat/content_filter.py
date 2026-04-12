"""Spam-oriented content filtering for chat messages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

_URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)
_EMAIL_PATTERN = re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b")


@dataclass(frozen=True)
class ContentFilterResult:
    """Structured content filter decision."""

    allowed: bool
    reason: str | None = None


class SpamContentFilter:
    """Detect clear spam/phishing patterns while allowing normal chat use-cases."""

    PHISHING_DOMAINS = {
        "spam.ru",
        "malware.net",
        "phishing.example",
    }
    SHORTENER_DOMAINS = {
        "bit.ly",
        "tinyurl.com",
        "shorte.st",
        "t.co",
        "goo.gl",
    }

    def __init__(
        self,
        *,
        repeated_same_url_threshold: int = 3,
        shortener_abuse_threshold: int = 5,
        caps_min_length: int = 50,
        caps_ratio_threshold: float = 0.7,
    ) -> None:
        self.repeated_same_url_threshold = repeated_same_url_threshold
        self.shortener_abuse_threshold = shortener_abuse_threshold
        self.caps_min_length = caps_min_length
        self.caps_ratio_threshold = caps_ratio_threshold

    def evaluate(self, content: str) -> ContentFilterResult:
        """Evaluate message text and return allow/block decision with reason."""
        normalized = content.strip()
        if not normalized:
            return ContentFilterResult(allowed=True)

        urls = _URL_PATTERN.findall(normalized)
        domains = [self._extract_domain(url) for url in urls]

        phishing_hit = self._find_phishing_domain(domains)
        if phishing_hit is not None:
            return ContentFilterResult(allowed=False, reason="phishing_domain_detected")

        if self._has_repeated_url_spam(domains):
            return ContentFilterResult(allowed=False, reason="repeated_url_pattern")

        if self._is_shortener_abuse(domains):
            return ContentFilterResult(allowed=False, reason="shortener_abuse")

        if self._is_all_caps_spam(normalized):
            return ContentFilterResult(allowed=False, reason="all_caps_spam")

        # Explicitly allow common legitimate formats with a single URL/email.
        if len(urls) <= 1 and _EMAIL_PATTERN.search(normalized):
            return ContentFilterResult(allowed=True)

        return ContentFilterResult(allowed=True)

    def _extract_domain(self, url: str) -> str:
        parsed = urlparse(url)
        return (parsed.netloc or "").lower().strip(".")

    def _find_phishing_domain(self, domains: list[str]) -> str | None:
        for domain in domains:
            if not domain:
                continue
            if any(
                domain == blocked or domain.endswith(f".{blocked}")
                for blocked in self.PHISHING_DOMAINS
            ):
                return domain
        return None

    def _has_repeated_url_spam(self, domains: list[str]) -> bool:
        if not domains:
            return False
        counts: dict[str, int] = {}
        for domain in domains:
            if not domain:
                continue
            counts[domain] = counts.get(domain, 0) + 1
            if counts[domain] > self.repeated_same_url_threshold:
                return True
        return False

    def _is_shortener_abuse(self, domains: list[str]) -> bool:
        shortener_hits = 0
        for domain in domains:
            if domain in self.SHORTENER_DOMAINS:
                shortener_hits += 1
        return shortener_hits > self.shortener_abuse_threshold

    def _is_all_caps_spam(self, content: str) -> bool:
        if len(content) < self.caps_min_length:
            return False

        letters = [char for char in content if char.isalpha()]
        if not letters:
            return False

        uppercase = sum(1 for char in letters if char.isupper())
        ratio = uppercase / len(letters)
        return ratio > self.caps_ratio_threshold
