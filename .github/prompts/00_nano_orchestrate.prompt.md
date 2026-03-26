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
5. Merge and clean up branch (equivalent to `04_nano_merge`), with two sub-steps:
   a. **Conflict check**: Before merging, verify PR `mergeable` status. If `CONFLICTED`, resolve via `git merge origin/main`, fix conflicting files, commit and push. Abort and report if non-resolvable.
   b. Merge once `MERGEABLE`, delete remote branch, sync local `main`.
6. Post-merge CI verification:
   - Poll CI status on `main` every 30 seconds (timeout: 10 minutes).
   - If CI fails: diagnose via `gh run view --log-failed`, apply targeted hotfix commits, re-verify.
   - If still failing after 2 fix attempts: stop as `blocked` and report exact failures and recovery action.

# Approval gates

- Stop after implementation and ask for approval to continue with commit/push.
- Stop after review-fix stage and ask for approval to continue with merge.

# Required reporting

- Show stage status and key artifacts (branch, commits, PR number)
- Show checks/tests outcomes (`Checks`, `Test: Verified`)
- Show post-merge CI status on `main`
- Show blockers and exact next step if workflow cannot continue
