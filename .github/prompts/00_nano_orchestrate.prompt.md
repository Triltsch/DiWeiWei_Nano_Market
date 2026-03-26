---
name: 00_nano_orchestrate
description: Orchestrate the full nano workflow from implementation to merge
agent: nano-orchestrator
---

# Objective

> Your goal is to orchestrate the complete workflow for an issue from implementation through merge with clear approval gates.

# Usage

- `/00_nano_orchestrate Issue #123`
- `/00_nano_orchestrate Issue #123, PR #130`

# Workflow

Execute the following stages in sequence:

1. Implement changes (equivalent to `01_nano_implement`)
2. Commit and push (equivalent to `02_nano_commit`)
3. Wait for Copilot review readiness via polling:
   - Poll interval: 60 seconds
   - Condition: new review/comments from Copilot reviewer are available
   - Timeout: 30 minutes (then stop as blocked with recovery hint)
4. Address PR review comments (equivalent to `03_nano_review`)
5. Merge and clean up branch (equivalent to `04_nano_merge`)

# Approval gates

- Stop after implementation and ask for approval to continue with commit/push.
- Stop after review-fix stage and ask for approval to continue with merge.

# Required reporting

- Show stage status and key artifacts (branch, commits, PR number)
- Show checks/tests outcomes (`Checks`, `Test: Verified`)
- Show blockers and exact next step if workflow cannot continue
