---
name: 03_nano_review
description: Fetch and implement the reviewer suggestions from a pull request
agent: mcp-pr-review
---

# Objective

> Your goal is to fetch and implement the suggestions a reviewer has left on a pull request

# Workflow

Given a pull request, perform the necessary steps in the following order:

## Implementation

- Ask for the pull request URL or ID. If the user provides a URL, extract the pull request ID from the URL.
- Check if the current branch is the branch the pull request relates to. If not, switch to the correct branch.
- Check if the pull request is already closed. In this case, check if the reviewer suggestions were already implemented or are outdated. For the suggestions which are not implemented yet and not outdated, assume that they were added to the PR after the PR was closed and merged. Open a new branch, implement the suggestions and create a new PR in this case.
- **REQUIRED: Use ONLY MCP GitHub tools (sequentially, NO parallels)** to fetch PR data. This ensures stable, reliable API communication. Never use fallback methods or manual GitHub CLI unless MCP is completely unavailable.
- **Read through peer review related comments carefully**: Review comments may be returned in different API responses than general issue comments.
- **NO fallback methods allowed** unless all 4 MCP calls above complete AND return no results. In that case, only then escalate to authenticated GitHub CLI or user-provided review links.
- **Copilot AI review handling:** Treat Copilot AI review comments exactly like human inline review comments. They are required input and must be implemented unless outdated or explicitly declined by the user.
- **Stopping rule:** Only conclude "no reviewer comments" AFTER completing all 4 MCP calls above. Document exact call sequence and result counts in final report.
- Implement the suggested changes in the codebase following the project guidelines and best practices.
- Analyze why the suggested changes were found in a pull request only and not during the initial implementation. Add appropriate learnings and tests if this can prevent similar issues in the future.

### Mandatory MCP-based comment discovery sequence (sequential calls only)

1. Call `mcp_github_get_pull_request(owner, repo, pullNumber)` to fetch base PR metadata (`state`, `title`, `head`, `base`).
2. Call `mcp_github_get_pull_request_reviews(owner, repo, pullNumber)` to fetch all review summaries.
3. Call `mcp_github_get_pull_request_review_comments(owner, repo, pullNumber)` to fetch all inline review threads with full context (`isResolved`, `isOutdated`, `author`, `body`, `path`, `line`).
4. Call `mcp_github_get_pull_request_comments(owner, repo, pullNumber)` to fetch general PR comments (non-review comments).
5. Filter results: keep only unresolved and non-outdated comments for implementation.
6. If there are no actionable comments after step 5: this is normal. Document which calls returned empty and proceed to the branch check / final reporting.

### Tool-availability rule (priority order)

1. **Primary**: Use MCP GitHub tools (`mcp_github_get_pull_request`, `mcp_github_get_pull_request_reviews`, `mcp_github_get_pull_request_review_comments`, `mcp_github_get_pull_request_comments`).
2. **Fallback 1**: If MCP tools are unavailable, use `github-pull-request_activePullRequest` from the VS Code GitHub PR extension.
3. **Fallback 2**: If both are unavailable, use `gh pr view` CLI commands.
4. Always report which method was used in the final response.

## Check and tests

- Run checks. Fix all warnings and errors before proceeding to the next step.
- **Run tests via the VSCode `Test: Verified` task** (not the raw `Test` task). This ensures infrastructure is healthy before running tests:
  - `Test: Verified` starts Docker services, waits for health checks (Redis + PostgreSQL connectivity), then runs pytest
  - Prevents false passes due to missing infrastructure (e.g., Redis connection errors masked by truncated output)
  - Fails fast with clear messaging if services cannot start
  - Only use raw `Test` task if you've manually confirmed Docker services are running and healthy
- Fix all warnings and errors before proceeding to the next step.
- **Important for Windows/PowerShell users**: The `Test: Verified` task is designed for PowerShell on Windows and automatically manages Docker Compose lifecycle. Ensure Docker Desktop is running before executing the task.

## Commit and push

- If the suggestion implementation led to additional important learnings, add these learnings to the `LEARNINGS.md` file in the root of the repository.
- Commit the changes to the current branch. 
- Push the committed changes to the remote repository.

## Required reporting in final response

- List the exact review comments implemented (with links when available).
- If any review comment could not be fetched automatically, state which fallback source was used.
- If no comments were found after full discovery, explicitly state which discovery steps were executed.

# Hints

- **Development environment**: This project is primarily developed on Windows using PowerShell. VSCode tasks and automation scripts are written for PowerShell execution. Adjust commands accordingly if working on macOS/Linux (use `bash` instead of `pwsh`, adjust path separators from `\` to `/`).
- **Critical Windows-specific practices**:
  - Always use `Test: Verified` task instead of raw `Test` to ensure Docker services are healthy before running tests. False test passes occur when tests run before Redis/PostgreSQL are ready (infrastructure readiness is mandatory, not optional).
  - Line ending handling: Tests and checks enforce LF line endings via Black/isort. Windows text editors may introduce CRLF; let the formatting tools normalize automatically.
  - PowerShell execution: Some Docker Compose commands and health checks use PowerShell-specific syntax. Direct terminal manipulation (e.g., via shell scripts) may fail; prefer VSCode tasks or Python scripts for cross-platform compatibility.
