# CI/CD Architecture

This document describes the GitHub Actions setup for the project.

## Overview

The CI/CD pipeline is split into focused workflows:

- `.github/workflows/ci.yml`: master workflow for pull requests and pushes.
- `.github/workflows/tests-backend.yml`: backend tests, formatting, linting, and security checks.
- `.github/workflows/tests-frontend.yml`: frontend build, tests, coverage gate, and linting.
- `.github/workflows/docker-build.yml`: container build, vulnerability scan, SBOM generation, and publish to GHCR.

## Workflow Responsibilities

### Master workflow: `ci.yml`

- Triggered on pull requests to `main` and pushes to `main` or `develop`.
- Runs a secret scan (gitleaks) first.
- Calls reusable backend and frontend workflows.
- Fails if backend or frontend workflow fails.
- Posts a summary comment on pull requests with backend and frontend coverage values.

### Backend workflow: `tests-backend.yml`

- Runs with Python 3.11.
- Installs backend dev dependencies from `pyproject.toml`.
- Executes pytest with coverage gate: `--cov-fail-under=80`.
- Enforces:
  - `black --check app tests`
  - `isort --check-only app tests`
  - `pylint app`
  - `bandit -r app`
- Publishes backend coverage as workflow output and PR comment.

### Frontend workflow: `tests-frontend.yml`

- Runs with Node.js 20 and `npm ci`.
- Runs `npm run build` to verify TypeScript build.
- Runs vitest in CI mode with coverage output.
- Reports frontend line coverage as a CI metric.
- Runs `npm run lint`.
- Publishes frontend coverage as workflow output.

### Docker workflow: `docker-build.yml`

- Triggered on pushes to `main` and semantic version tags (`v*.*.*`).
- Builds scan image and runs Trivy vulnerability scan (high/critical severity).
- Uploads Trivy SARIF results.
- Builds and pushes multi-arch image to GHCR:
  - `ghcr.io/<owner>/diweiwei-nano-market:latest` (main only)
  - `ghcr.io/<owner>/diweiwei-nano-market:vX.Y.Z` (tags)
  - `ghcr.io/<owner>/diweiwei-nano-market:sha-<commit>`
- Generates and stores SBOM artifact.

## Branch Protection Recommendations

Configure required status checks on `main`:

- `Secret scan (gitleaks)`
- `Backend pipeline / Backend test, lint, and security gates`
- `Frontend pipeline / Frontend build, test, and lint`
- `CI summary and policy checks`

This ensures no pull request can be merged if tests, lint, coverage gates, or secret scanning fail.

## Local Parity Commands

Developers can run the same quality gates locally:

```bash
# Backend
python -m pytest tests/ -v --cov=app --cov-fail-under=80
python -m black --check app tests
python -m isort --check-only app tests
python -m pylint app
python -m bandit -r app -x tests,migrations

# Frontend
cd frontend
npm ci
npm run build
npm run test -- --run --coverage.enabled=true --coverage.provider=v8 --coverage.reporter=text --coverage.reporter=json-summary
npm run lint
```

## Notes

- Coverage comments are posted on pull requests by GitHub Actions.
- `docker-build.yml` is intentionally separated from PR validation because publishing should happen only after merge to `main` or release tagging.
