---
name: nano_implement
description: Perform an implementation task
agent: agent
---

# Objective

> Your goal is to implement a new feature or fix a bug.

# Workflow

Perform the necessary steps in the following order:

## Access issue details

- If an issue is given to be implemented, access the issue tracker using the MCP interface and read the issue description as well as all comments to get the full context about the issue.
- If you are asked to implement an issue step only, look for hints left by a prior agent instance in the issue comments. Implement that step only.
- Check if we are working on the `main` branch. Warn if not so and offer to switch to `main` branch. If the user wants to switch, switch to the `main` branch.
- Perform all implementation work directly on the `main` branch. Do not create feature branches unless explicitly instructed.

## Access learnings

- Read the `LEARNINGS.md` file in the project root to get important learnings from prior implementations rounds.



## Implementation

- Perform your implementation tasks, following the best practices.
- For new features or solved bugs, add tests or test cases matching the structure of the existings tests. Be thorough, but do not cover every detail with a test. Make a reasonable decision what is necessary for being tested.

## Validation

- Run checks via the VSCode `Checks` task.
- Fix all errors and warnings reported by the checks. Repeat until all checks pass.
- Run tests via the VSCode `Test` tasks.
- Fix any failing tests including all warnings. Repeat until all tests pass.

## Environment Validation

- **Verify development environment integrity:**
  - Validate that Docker services can start successfully: run `docker compose pull` to verify all images are available, then `docker compose up -d` and verify all containers reach healthy status within a reasonable time
  - Check for configuration consistency issues:
    - Credential alignment across related services (e.g., MinIO server credentials must match MinIO CLI init credentials, database passwords must align with connection strings)
    - Port mapping consistency (verify `docker-compose.yml` port mappings match application config expectations)
    - Volume naming consistency (ensure no orphaned volumes with old naming schemes that could cause conflicts)
    - Image tag validity (verify pinned image tags are still available on registries; use latest or stable version tags if specific releases become unavailable)
  - Document any issues found in the terminal output and propose fixes
  - Run `docker compose down` after validation to clean up the test environment

- **Review configuration files for common pitfalls:**
  - Check `docker-compose.yml` for hardcoded secrets vs. environment variables (prefer env vars with sensible defaults)
  - Look for version mismatches between Docker images and persistent data (incompatible database versions in volumes cause startup failures)
  - Scan `.env` and `.env.example` for alignment with application config loading
  - Verify that all environment-dependent configurations can be discovered from documentation
  - Check for environment variable value inconsistencies between services (e.g., different defaults in different places)

- **Validate test execution environment:**
  - Ensure tests pass both with and without manual environment variable setup
  - Verify that configuration loading happens at the right time in the test lifecycle
  - Check for any environment-dependent test flakiness or port conflicts

## Adapt documentation

- Scan the documentation for inconsistencies and necessary adaptions triggered by this issues changed.
- Adapt the documentation accordingly to reflect the changes made.

# Hints

- Complain if the current setup is not sufficient for performing an implementation. Make a proposal on how to enhance the situation than.
- Do **not** commit the changes yet. They will be reviewed in a manual process and then committed by a later agent instance. Focus on the implementation and leave the committing to a later stage.