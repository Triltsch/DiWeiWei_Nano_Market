---
name: nano_review
description: Fetch and implement the reviewer suggestions from a pull request
agent: agent
---

# Objective

> Your goal is to fetch and implement the suggestions a reviewer has left on a pull request

# Workflow

Given a pull request, perform the necessary steps in the following order:

## Implementation

- Ask for the pull request URL or ID. If the user provides a URL, extract the pull request ID from the URL.
- Check if the current branch is the branch the pull request relates to. If not, switch to the correct branch.
- Check if the pull request is already closed. In this case, check if the reviewer suggestions were already implemented or are outdated. For the suggestions which are not implemented yet and not outdated, assume that they were added to the PR after the PR was closed and merged. Open a new branch, implement the suggestions and create a new PR in this case.
- **Read through peer review related comments carefully**: Review comments may be returned in different API responses than general issue comments.
- **Mandatory comment discovery sequence (do not skip):**
	1. Fetch the active pull request metadata.
	2. Fetch the pull request by issue/PR number.
	3. Check all returned fields for review content: comments, timeline comments, reviews, threads, inline suggestions, and bot reviews.
	4. **Search for specialized MCP GitHub tools**: Use `tool_search_tool_regex` with pattern `mcp_github.*review|pull_request.*review` to discover tools like `mcp_github_pull_request_read` which provides the `get_review_comments` method for fetching inline review threads with full context (isResolved, isOutdated, isCollapsed, author, body, path, line).
	5. If available, call `mcp_github_pull_request_read` with method `get_review_comments` to fetch all review threads. This returns the complete review data structure that standard PR fetch methods do not expose.
	6. If no review comments are found after steps 1-5 but the user indicates comments exist in the PR UI, assume API coverage is incomplete and continue with fallback discovery.
- **Fallback discovery when standard methods do not expose review threads:**
	- **First**: Search for and use specialized MCP GitHub tools (see step 4 above) before attempting other methods.
	- **Second**: If available in the environment, use authenticated GitHub CLI/API to query review threads.
	- **Last resort**: Ask the user for direct review-comment links or screenshots of each unresolved thread.
	- If authenticated access is not available, explicitly state this limitation and continue using user-provided review content as source of truth.
- **Copilot AI review handling:** Treat Copilot AI review comments exactly like human inline review comments. They are required input and must be implemented unless outdated or explicitly declined by the user.
- **Stopping rule:** Never conclude "no reviewer comments" after a single API call. Only conclude this after all discovery steps above are completed and results are documented.
- Implement the suggested changes in the codebase following the project guidelines and best practices.
- Analyze why the suggested changes were found in a pull request only and not during the initial implementation. Add appropriate learnings and tests if this can prevent similar issues in the future.

## Check and tests

- Run all checks. Fix all warnings and errors before proceeding to the next step.
- Run all tests. Fix all warnings and errors before proceeding to the next step.

## Commit and push

- If the suggestion implementation led to additional important learnings, add these learnings to the `LEARNINGS.md` file in the root of the repository.
- Commit the changes to the current branch. 
- Push the committed changes to the remote repository.

## Required reporting in final response

- List the exact review comments implemented (with links when available).
- If any review comment could not be fetched automatically, state which fallback source was used.
- If no comments were found after full discovery, explicitly state which discovery steps were executed.
