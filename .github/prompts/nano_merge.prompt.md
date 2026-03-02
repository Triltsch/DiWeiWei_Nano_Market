---
name: nano_merge
description: Perform a merge task
agent: agent
---

# Objective

> Your goal is to merge a pull request into the main branch, delete the development branch and switch to the main branch.

# Workflow

Perform the necessary steps in the following order:

## Access issue details

- If an PR is given to be merged, access the PR tracker using the MCP interface and read the PR description as well as all comments to get the full context about the PR.
## Merge PR
- Merge the PR into the main branch using the GitHub interface. If there are merge conflicts, resolve them and then merge the PR.
## Delete development branch
- After the PR is merged, delete the development branch that was used for the PR.
## Switch to main branch
- Switch to the main branch to ensure that you are working on the latest codebase.


