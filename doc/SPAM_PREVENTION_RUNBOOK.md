# Spam Prevention Runbook

## Purpose

This runbook describes the active anti-spam controls for chat messaging and how to validate them during operations and QA.

## Active Controls

1. API chat rate limiting
- Endpoint: `POST /api/v1/chats/{session_id}/messages`
- Scope: per user and per chat session key
- Window: `RATE_LIMIT_CHAT_MESSAGE_WINDOW_SECONDS` (default 60 seconds)
- Base limit: `RATE_LIMIT_CHAT_MESSAGE_MAX_REQUESTS` (default 10)
- Burst: `RATE_LIMIT_CHAT_MESSAGE_BURST_REQUESTS` (default 3)
- Violation response: HTTP 429 with `Retry-After` header and user-facing backoff detail

2. Chat content filtering
- Blocks known phishing domains
- Blocks repeated same-domain URL patterns above threshold
- Blocks URL shortener abuse above threshold
- Blocks extreme all-caps spam messages
- Violation response: HTTP 400 with `Message blocked: <reason>`

3. Reverse proxy limits (Nginx)
- Chat messages: 60 req/min (burst 10)
- Nano ratings: 10 req/min (burst 10)
- Login: 5 req/min (burst 3)
- Default API: 100 req/min (burst 20)
- Violation response: HTTP 429 with `Retry-After: 60`

4. Monitoring
- `spam_message_rate_limit_429_total{endpoint="POST /api/v1/chats/{session_id}/messages"}`

## Quick Validation Steps

1. Backend checks
- Run backend validation commands used by CI/release checks (format/lint/tests) and confirm success before release.

2. Integration verification
- Run repository integration/verification checks in CI, or verify the latest successful CI run for the target environment.
- Confirm no unhealthy/restarting containers during startup

3. Manual API smoke checks
- Send <= 10 messages/minute + small burst in one session: requests succeed
- Exceed the threshold in the same session: HTTP 429 + `Retry-After`
- Send phishing URL (`https://spam.ru/...`): HTTP 400 and block reason

4. Frontend UX check
- Trigger chat 429 in UI
- Confirm send input/button is disabled during countdown and re-enabled afterward

## Configuration Notes

- Keep backend and Nginx limits aligned when tuning thresholds.
- For local testing, use environment variables to override defaults instead of code edits.
- If rate-limit behavior appears inconsistent, verify clock drift and proxy header trust configuration.
