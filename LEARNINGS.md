# Learnings - DiWeiWei Nano-Marktplatz Projekt

## Sprint 3 Story 2.4: Nano Status Workflow (Issue #52)

### Context
Implemented status workflow for Nanos enabling creators to manage lifecycle from draft to published with state machine validation, metadata completeness checks, and audit logging. Built PATCH `/api/v1/nanos/{nano_id}/status` endpoint with comprehensive business rules.

### Key Learnings

#### 1. **State Machine Pattern in Business Logic**
- **Implementation**: Explicit allowed transitions map in service layer with validation function
- **Pattern Used**: 
  - Define allowed transitions dictionary: `{"draft": ["pending_review", "published", ...], ...}`
  - Separate validation function for transition rules (`_validate_status_transition()`)
  - Special rules (24h unpublish window) implemented as conditional checks
- **Benefit**: Clear business rules, easy to test, maintainable state machine
- **Learning**: State machines belong in service layer, not database constraints. Use explicit transition maps rather than implicit checks. Document allowed transitions in endpoint description and test all edges. Pattern: `allowed_transitions[old_status]` lookup with special condition handling.

#### 2. **Metadata Completeness Validation for Publishing**
- **Observation**: Publishing requires complete metadata (title, description, duration, language)
- **Implementation choice**:
  - Validation only on draft → published transition
  - Separate `_validate_metadata_completeness()` function
  - Checks required fields are present and non-empty
  - Returns clear error message listing missing fields
- **Alternative considered**: Schema-level NOT NULL constraints (rejected - metadata can be incomplete in draft)
- **Learning**: Conditional validation based on state transitions. Don't enforce completeness globally - allow drafts to be incomplete. Provide actionable error messages listing exactly what's missing. Pattern: dedicated validation function called before state transition, not in schema.

#### 3. **Timezone-Aware Datetime Handling**
- **Problem**: Comparing `datetime.now(timezone.utc)` with database timestamp caused `TypeError: can't subtract offset-naive and offset-aware datetimes`
- **Root Cause**: SQLAlchemy may return timezone-naive datetimes depending on database/column configuration
- **Solution**: Normalize timezone before comparison:
  ```python
  published_at = nano.published_at
  if published_at.tzinfo is None:
      published_at = published_at.replace(tzinfo=timezone.utc)
  time_since_publish = datetime.now(timezone.utc) - published_at
  ```
- **Learning**: Always check `tzinfo` before comparing datetimes. PostgreSQL's `timestamp with time zone` returns timezone-aware, but `timestamp without time zone` doesn't. Normalize at comparison point rather than at storage. Pattern: defensive timezone handling in business logic, not at ORM level.

#### 4. **Audit Logging Integration**
- **Pattern**: Log status changes via `AuditLogger.log_action()` after successful commit
- **Metadata captured**: `field`, `old_value`, `new_value`, `reason` (optional)
- **Benefit**: Complete audit trail of status changes for compliance/debugging
- **Learning**: Audit logging after commit (not before) ensures transaction succeeded. Include optional reason field for context. Use existing `AuditAction.DATA_MODIFIED` for field changes. Pattern: `await AuditLogger.log_action(session=db, action=..., metadata={...})` immediately after commit.

#### 5. **Test Fixture Dependency Management**
- **Problem**: Status workflow tests needed authenticated user token, but no `access_token` fixture existed
- **Solution**: Created `access_token` fixture that depends on `verified_user_id` and `test_user_data`, logs in, returns token
- **Pattern**:
  ```python
  @pytest.fixture
  async def access_token(async_client, verified_user_id, test_user_data) -> str:
      login_response = await async_client.post("/api/v1/auth/login", json={...})
      return login_response.json()["access_token"]
  ```
- **Learning**: Reusable token fixtures reduce test boilerplate and ensure consistent auth setup. Fixture dependencies (verified_user_id) automatically create user before login. One fixture, many tests. Pattern: fixture for common test prerequisites.

#### 6. **Timestamp Management for State Transitions**
- **Pattern**: Set `published_at` when transitioning to published, `archived_at` when transitioning to archived
- **Implementation**: 
  - Check if timestamp already set (only set on first transition to that state)
  - Use `datetime.now(timezone.utc)` for consistency
  - Timestamps returned in API response for client awareness
- **Learning**: Timestamps track state transition history. Don't overwrite existing timestamps (preserve original publish date). Always use timezone-aware datetimes for consistency. Pattern: `if nano.published_at is None: nano.published_at = datetime.now(timezone.utc)` before commit.

#### 7. **No-Op Status Updates for Idempotency**
- **Design choice**: Allow updating status to same status (no-op)
- **Implementation**: Early return when `old_status == new_status`
- **Benefit**: Idempotent API - client can retry without side effects
- **Learning**: Idempotent APIs are safer for retry scenarios. No-op check before validation reduces unnecessary processing. Return success (200) with both old/new status matching. Pattern: `if old_status == new_status: return nano, old_status, new_status` at start of function.

#### 8. **Test Organization for Feature Completeness**
- **Approach**: Separate test file for status workflow (`test_status_workflow.py`) vs. metadata tests (`test_nanos_routes.py`)
- **Structure**: 13 tests covering:
  - Valid transitions (5 tests)
  - Invalid transitions (2 tests)
  - Authorization boundaries (2 tests)
  - Metadata completeness (1 test)
  - Edge cases (3 tests: no-op, 404, invalid value)
- **Coverage**: All state transitions tested, all error paths verified, audit logging confirmed
- **Learning**: Organize tests by feature domain, not by endpoint. Comprehensive edge case coverage (24h boundary, no-op, invalid transitions) prevents production bugs. Test both happy paths and all error conditions. Pattern: one test class per feature, descriptive test names, verify database state + API response.

#### 9. **24-Hour Business Rule Implementation**
- **Requirement**: Published → draft only allowed within 24h of publication
- **Implementation**: Calculate time delta, compare to 24 * 3600 seconds
- **Error message**: Clear guidance ("Use 'archived' status instead")
- **Learning**: Time-based business rules need clear error messages with alternatives. Use seconds for comparison (avoids floating point issues with hours). Test both sides of boundary (within 24h succeeds, after 24h fails). Pattern: delta calculation with clear threshold comparison and actionable error.

#### 10. **OpenAPI Documentation for State Machines**
- **Documentation approach**:
  - List all valid transitions in endpoint description
  - Document special rules (24h, metadata completeness)
  - Provide clear error descriptions for each validation
  - Include example request/response with status change
- **Benefit**: Clients understand state machine without reading code
- **Learning**: State machines need comprehensive documentation - list transitions, special rules, error scenarios. FastAPI auto-generates from docstrings but requires explicit detail. Example: "draft → pending_review, published, archived, deleted" shows all options at a glance. Pattern: endpoint docstring with structured "Valid Status Transitions" section.

### Implementation Stats
- **Files Created**: 1 (test_status_workflow.py)
- **Files Modified**: 4 (schemas.py, service.py, router.py, conftest.py)
- **Test Coverage**: 13 new tests, all passing; 266 total tests ✅
- **Lines Added**: ~600 (including tests and documentation)
- **State Transitions**: 14 valid paths, 5 status values
- **Business Rules Enforced**: 4 (creator-only, state machine, 24h window, metadata completeness)

### Process Observations
- **Black formatting caveat**: Auto-formatter can incorrectly nest new classes if patch indentation is ambiguous - verify top-level classes remain top-level after formatting
- **Timezone handling discovered via tests**: TDD caught naive/aware datetime mismatch that might have been production bug
- **Audit logging integration seamless**: Existing AuditLogger service worked perfectly without modification
- **Test fixture pattern accelerated testing**: access_token fixture eliminated repetitive login code across 13 tests

### Design Decisions Documented
- **Why state machine in service layer**: Business rules change; service layer is more flexible than database triggers/constraints
- **Why 24-hour window**: Balance between creator flexibility and content stability for consumers
- **Why separate validation functions**: Testability and clarity - each validation concern isolated
- **Why allow no-op status updates**: API idempotency for safe retries
- **Why timestamps on first transition only**: Preserve historical publish dates, not latest re-publish

---

## Sprint 2 Story 2.2: Nano Metadata Capture (Issue #53)

### Context
Implemented comprehensive API endpoints for Nano metadata capture and retrieval as part of Sprint 2 story planning. The requirement involved creating REST endpoints that respect draft-only metadata editing, implement comprehensive validation, and maintain proper authorization boundaries. This story established several patterns for service-layer business logic and test infrastructure that will inform future feature implementations.

### Key Learnings

#### 1. **Service-Layer Pattern Separates Concerns Effectively**
- **Observation**: Implementing business logic strictly in service layer (not router or model) made authorization and validation testable in isolation
- **Pattern Used**: 
  - Router layer handles HTTP concerns (dependency injection, status codes, response formatting)
  - Service layer handles business logic (authorization checks, state validation, field mutations)
  - Model layer (SQLAlchemy ORM) handles persistence only
- **Benefit**: Authorization and validation behavior is exercised via `async_client`-based route tests that drive the service layer through FastAPI's dependency injection and test database session fixtures, while still allowing the service layer to be unit tested independently if needed
- **Learning**: Clear separation of concerns yields testable code. Authorization failures (403) vs. validation failures (400) vs. not-found (404) are distinct business logic, not just HTTP status codes. Implement them in service layer so they can be verified both via focused unit tests and end-to-end route tests.

#### 2. **Test Infrastructure Must Mirror Production Dependency Injection**
- **Problem**: Initial test run returned 404 on all nanos endpoints despite implementation being correct
- **Root Cause**: Test app fixture in `conftest.py` didn't include nanos router—only auth/audit/upload routers were registered
- **Why it wasn't caught earlier**: Router registration happens implicitly in app initialization, so "it worked" during manual testing (app/main.py includes router), but test fixture was incomplete
- **Solution**: Added `app.include_router(get_nanos_router())` to test app fixture in conftest.py
- **Learning**: Test fixtures are contracts—any dependency injected in production must be present in test fixtures, or tests will have false failures. The pattern: if it's in `main.py`, it must be in `conftest.py`'s test app. Use grep to verify router registration completeness: `grep -r "include_router" app/main.py tests/conftest.py` should show consistent router lists.

#### 3. **Draft-Status Validation: Business Logic, Not Database Constraints**
- **Observation**: Draft-only metadata editing is a business rule, not a database constraint
- **Implementation choice**: 
  - Service layer validates `if nano.status != NanoStatus.DRAFT: raise HTTPException(400, ...)`
  - Not enforced via database trigger or unique constraint
  - Allows other services to potentially manage published Nano metadata without triggering constraint violations
- **Alternative considered**: Database NOT NULL constraint on metadata frozen_at timestamp when status = published
- **Reasoning**: Business rules change; database constraints are hard to modify. Keeping validation in service layer provides flexibility
- **Learning**: Stateful business rules (draft-only editing, published-immutable) belong in service layer, not schema constraints. This allows incremental feature evolution (future: Sprint 3 could add update broadcasts to editors when Nano publishes, without schema changes).

#### 4. **Authorization Boundary: Creator-Only Access**
- **Pattern established**: `if nano.creator_id != current_user_id: raise HTTPException(403, ...)`
- **Not checked by**: Router layer (doesn't know about Nano ownership), middleware (too early, no context), database (no constraint)
- **Always checked by**: Service layer before any modification
- **Test coverage**: Both happy path (creator updates own nano) and failure path (other user gets 403) tested explicitly
- **Learning**: Ownership-based authorization belongs in service layer where business entities are known. Middleware is too generic; routers are too shallow. Service layer knows about Nano objects and their creator fields—the right place for this check. Pattern: every service function that modifies a user-owned resource should have a `current_user_id` parameter and ownership check.

#### 5. **Field-Level Validation Must Support Partial Updates**
- **Pattern**: MetadataUpdateRequest has all fields optional (`title: str | None = None`)
- **Benefit**: Clients can update single fields without providing full object
- **Tracking mechanism**: Service returns `updated_fields: list[str]` showing which fields were modified
- **Test coverage**: Tests verify that only provided fields are updated (other fields unchanged), and updated_fields list matches actual changes
- **Learning**: The metadata update endpoint must support partial updates explicitly, even though it is implemented as a POST (`POST /api/v1/nanos/{nano_id}/metadata`) rather than a PATCH. Make all fields optional in the request schema, track which fields changed, and return that in the response—client knows what was modified, useful for optimistic UI updates. Pattern: `if metadata.field_name is not None: object.field_name = metadata.field_name; updated_fields.append("field_name")`

#### 6. **Enum Mapping at Service Boundary**
- **Challenge**: Database stores enums as Python enum objects (`CompetencyLevel.BASIC`), but API responses need strings like `"beginner"`
- **Solution location**: Service layer, not router or model property
- **Implementation**: Use an explicit mapping dict from `CompetencyLevel` (int enum) to API strings in response schema building, for example: `competency_level = COMPETENCY_LEVEL_API_MAPPING[competency_level] if competency_level is not None else None`
- **Why not in model**: SQLAlchemy models should represent storage format (enums as objects)
- **Why not in Pydantic**: Pydantic is for schema validation; enum mapping is business logic
- **Learning**: Data format transformations (database format → API format) happen at service boundaries. Create `NanoMetadataResponse` from the raw Nano object using an explicit enum-to-string mapping dict, rather than relying on `.value` or implicit serialization. Pattern: service builds response objects with explicit transformations, not implicit serialization.

#### 7. **Category Assignments: Many-to-Many Creates Complexity**
- **Observation**: Categories are many-to-many via NanoCategoryAssignment junction table
- **Update pattern challenges**:
  - Delete old assignments by first loading them via `select(NanoCategoryAssignment).where(NanoCategoryAssignment.nano_id == nano_id)` and then calling `session.delete(assignment)` on each ORM instance in a loop
  - Create new assignments by instantiating `NanoCategoryAssignment` ORM objects for each `(nano_id, category_id, rank)` combination and adding them to the session
  - Must not leave assignments orphaned if validation fails mid-transaction; all deletes and inserts must occur within a single transaction
- **Test protection**: Tests verify old assignments are removed before new ones are added and that categories remain queryable via the GET endpoint after an update
- **Learning**: Many-to-many updates are atomic in a single transaction, but implemented as multiple ORM-level deletes/inserts rather than raw bulk SQL. Document the actual pattern clearly. For future: consider refactoring to true bulk `delete(...)`/`insert(...)` operations if profiling shows a need, and whether category ranking (assigning `rank` during update) needs versioning (Sprint 3: audit trail of category changes). Pattern: `db.begin_nested()` for savepoints if categories are optional fields; full transaction rollback if category validation fails.

#### 8. **Validation: Client-Side Limits vs. Server-Side Constraints**
- **Pydantic schema validates**:
  - `title`: max_length 200 (documented limit, parsed during request deserialization)
  - `description`: max_length 2000 (same)
  - `duration_minutes`: Field(gt=0) (must be positive)
  - `format`: Literal["video", "text", "quiz", ...] (enum)
  - `competency_level`: Literal["beginner", "intermediate", ...] (enum)
  - `language`: two-character ISO 639-1 code; length enforced via Field and value normalized to lowercase by a validator that also checks format (length 2, alphabetic only)
- **Service layer validates**:
  - Category IDs exist in database (FK doesn't auto-validate non-existent IDs in ORM without explicit query)
  - At most 5 categories assigned (business rule, not schema constraint)
- **Test coverage**: Both "valid within limits" and "invalid when exceeded" tested
- **Learning**: Pydantic handles format validation (types, lengths, enums, basic normalization); service handles business logic validation (existence, relationships, limits). Layered validation provides both tight error feedback (Pydantic 422 for malformed request) and business-logic feedback (service 400 for invalid state). Pattern: Pydantic first-pass (syntax), service second-pass (semantics).

#### 9. **Tests Revealed Infrastructure Dependency Ordering**
- **Observation**: Creating test users requires user_id UUID; creating nanos requires creator_id foreign key to users table
- **Fixture dependency graph**: `db_session` → `verified_user_id` → `nano_in_draft_status` 
- **Initial setup**: Tests created fixtures ad-hoc; later tests failed with FK constraint violations
- **Resolution**: Explicit fixture ordering in conftest.py (user fixture first, then nano fixture using user_id)
- **Learning**: Database fixtures need dependency ordering to avoid FK violations. Use pytest fixture request parameter to enforce ordering: `@pytest.fixture async def nano_in_draft_status(db_session, verified_user_id)` makes dependency explicit. Pattern: fixtures should be minimal and composed; complex test data built from simpler fixtures.

#### 10. **OpenAPI Documentation Reduces Support Burden**
- **Implementation**: FastAPI auto-generates from docstrings and Pydantic schemas, but explicit examples needed for clarity
- **Added documentation**:
  - Business rule: "Only draft Nanos may have metadata updated. Published Nanos have immutable metadata."
  - Error cases: 401 (auth required), 403 (not creator), 400 (not draft, validation failed), 404 (not found)
  - Example requests/responses with sample category assignments
- **Usage**: `/docs` endpoint shows interactive Swagger UI—clients can test endpoints directly
- **Learning**: OpenAPI documentation from code is low-friction. Invest 5 minutes in docstring examples and error descriptions; saves hours of client integration confusion. Pattern: FastAPI docstrings should include business rules and error scenarios in addition to parameter descriptions.

### Implementation Stats
- **Files Created**: 3 (schemas.py, service.py, router.py in app/modules/nanos/)
- **Files Modified**: 2 (app/main.py, tests/conftest.py)
- **Test Coverage**: 12 new tests, all passing; >80% coverage on nanos module
- **Test Results**: 252 tests passing (including 12 new nanos tests), 1 skipped ✅
- **Quality**: Black/isort compliant, no linting errors ✅
- **API Endpoints**: 2 implemented (GET /{nano_id}, POST /{nano_id}/metadata)
- **Validation Fields**: 8 (title, description, duration_minutes, competency_level, language, format, license_type, category_ids)
- **Business Rules Enforced**: 3 (creator-only, draft-only editing, metadata immutable when published)

### Process Observations
- **Test-driven validation discovery**: Adding missing assertions to tests revealed that short passwords can score "strong" if varied enough—validation logic working as implemented, but may need design review
- **Infrastructure-as-contract thinking**: Test fixture incompleteness exposed as 404s; fixed by ensuring test app matches production app's dependency chain
- **Patterns enable future consistency**: Service-layer auth checks, enum mapping, field tracking patterns established here will accelerate Story 2.4 (Publishing Workflow) implementation—create similar patterns for published Nano transitions

### Design Decisions Documented
- **Why creator_id in Nano table**: Enables ownership checks; alternative (JWT claim-based) rejected because Nano can outlive creator's login session
- **Why NanoCategoryAssignment.rank**: Allows future sorting of categories; MVP doesn't use it, but schema supports it
- **Why no soft-delete**: Nanos are immutable once published; can be archived/hidden but not deleted to maintain referential integrity
- **Why draft-only editing in service, not constraint**: Business rule flexibility; published Nanos might have admin-only metadata updates in future

---

## Frontend React Query Provider Review (Issue #35 - PR #49 Review Implementation)

### Context
After implementing React Query provider integration for Sprint 2, Copilot PR review reported 9 inline comments across tests and docs. Most findings were not functional bugs in production code, but quality gaps in test realism, strict typing, and documentation accuracy.

### Why these issues surfaced in PR review (and not initial implementation)
- **Shallow test coverage**: Hook tests only checked that a function existed instead of validating React Query behavior (`enabled: false`, `refetch` path).
- **Type safety drift in tests**: Temporary `any` casts were introduced to quickly satisfy interceptor test compilation, reducing strict-mode safety.
- **Documentation drift**: Markdown snippets were hand-written and not validated against real source code/config shape, causing stale/outdated examples.

### Actions taken

#### Test improvements:
1. **Refactored HTTP client test helpers** - Added proper type narrowing in `getRequestHandlers()`/`getResponseHandlers()` to avoid optional-chaining false positives and ensure assertions catch missing interceptors.
2. **Converted hook test to behavioral** - Replaced shallow symbol existence checks with `renderHook` + `QueryClientProvider` wrapper, executing actual hook lifecycle with mocked `httpClient.get`.
3. **Updated header validation test** - Simplified test to focus on testable configuration (baseURL/timeout) rather than checking axios internal header structure which isn't reliably exposed.

#### Documentation fixes:
1. **Fixed retryDelay snippet** - Corrected `(attempt)` parameter in exponential backoff example to match implementation.
2. **Updated Dependencies section** - Removed version numbers that were out of sync with actual package.json (React Query v5, Testing Library v16 vs. outdated v4/v14 in docs).
3. **Corrected QueryClient config example** - Fixed "To adjust defaults" snippet to show proper `defaultOptions.queries` nesting instead of flat structure.

#### Test typing improvements:
1. **Removed unused imports** - Cleaned up `expect` import from vitest.setup.ts (already available globally via @testing-library/jest-dom).
2. **Removed stub directive** - Removed unnecessary `eslint-disable` comment on `void error.config` in interceptors.ts.

### Test Results
- **All 11 frontend tests passing** (9 httpClient + 2 useUserProfile)
- **TypeScript strict mode (no errors)**
- **100% on reviewed file fixes**

### Process improvement
- For each new hook, require at least one behavioral test that verifies query lifecycle (disabled/enabled/refetch/error path), not only symbol existence.
- Avoid `any` in tests; use concrete library types even in mocks to keep strict-mode guarantees.
- Treat docs code blocks as executable contracts: copy from implementation or validate examples during review.
- When documenting config objects with nesting, run examples through real implementations first to catch structural mismatches.


## Frontend HTTP Client Review (Issue #34 - PR #48 Review Implementation)

### Context
After implementing the centralized Axios HTTP client for frontend (Issue #34, PR #48), received 9 Copilot AI review comments identifying critical issues with test reliability, documentation format, type safety, and configuration validation logic.

### Key Learnings

#### 1. **Import Hygiene - Export Locations Matter**
- **Problem**: Test imported `API_CONFIG` from `./httpClient` but that module doesn't export it - `API_CONFIG` is only exported from `./config`
- **Why it failed silently during implementation**: No TypeScript compilation without `npm install`, so import error wasn't caught
- **Solution**: Split imports: `import { httpClient } from "./httpClient"` and `import { API_CONFIG } from "./config"`
- **Learning**: Always import from the actual exporting module, not from re-export barrels unless intended. TypeScript catches this but only when dependencies are installed.

#### 2. **Async Test Assertions - Don't Skip await**
- **Problem**: Test called `handler.rejected(error)` in try/catch, expecting synchronous throw. But it returns a rejected Promise, so catch block never executes
- **Result**: Test always passed even if token clearing logic was completely broken
- **Solution**: Use `await expect(handler.rejected(error)).rejects.toBeInstanceOf(Error)` to properly handle async rejections
- **Learning**: Axios interceptors are async - test them with proper async handling or tests become false positives

#### 3. **Markdown Files Should Be Markdown, Not JS Comments**
- **Problem**: README.md wrapped in `/** ... */` JS comment syntax, rendering as literal text in Markdown viewers (GitHub, VS Code)
- **Root Cause**: Likely copy-pasted from a JSDoc comment template and never converted
- **Fix**: Remove all `/**`, `*/`, and leading ` * ` markers - write pure Markdown
- **Learning**: `.md` files are consumed by markdown renderers, not compilers. They should never contain language-specific comment syntax

#### 4. **Test Dependencies Must Match Test Runtime**
- **Problem**: Test file imported from `vitest` but package.json had no vitest dependency, and vite.config.ts had no test configuration
- **Why tests seemed to work during implementation**: Tests were never actually executed - just written
- **Solution**: 
  - Added `vitest@^3.0.0` and `@vitest/coverage-v8@^3.0.0` to devDependencies
  - Added `jsdom@^26.0.0` for DOM simulation
  - Added `test` section to vite.config.ts with `environment: "jsdom"`
  - Added `"test": "vitest"` script to package.json
- **Learning**: Frontend tests require explicit test runner setup. Unlike backend pytest (auto-discovered), Vite needs configuration.

#### 5. **Test Assertions Must Assert**
- **Problem**: "should inject access token" test ran interceptor, captured config, but never asserted the Authorization header value
- **Result**: Test always passed regardless of whether token injection worked
- **Fix**: Added `expect(capturedConfig.headers.Authorization).toBe(\`Bearer ${mockToken}\`)`
- **Learning**: Every test variable should have a corresponding assertion. If you capture a value, verify it. "Simplified test" comments often mean incomplete tests.

#### 6. **Unused Variables as Future Placeholders - Signal Intent**
- **Problem**: `const originalRequest = error.config;` defined but unused, causing TypeScript/linter warning
- **Context**: Variable is reserved for Sprint 3 token refresh logic
- **Solution**: Prefix with underscore: `const _originalRequest = error.config;` and add comment explaining it's for Sprint 3
- **Learning**: Use underscore prefix for intentionally-unused variables that document future implementation points. Keeps linters happy while preserving architectural intent.

#### 7. **Validation Logic Must Actually Validate**
- **Problem**: `validateApiConfig()` checked `if (!API_CONFIG.BASE_URL)` but this is always falsy because the config uses `??` default: `import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"`
- **Result**: Dead code - validation never triggers
- **Fix**: Check the source environment variable instead: `if (!import.meta.env.VITE_API_BASE_URL)` with warning (not error)
- **Why warning not error**: Defaults are intentional - we want to warn developers they're using defaults, not block execution
- **Learning**: When validating configuration with defaults, validate the input source, not the post-default value

#### 8. **Comment Clarity - Avoid Misleading Implications**
- **Problem**: Comment said "token is automatically injected by interceptor" on login request, implying token injection happens for this call
- **Reality**: Login acquires tokens - no token exists yet to inject. Interceptor checks for token and finds none.
- **Fix**: "This call obtains tokens; interceptor injects a token only if one already exists"
- **Learning**: Comments should describe what actually happens in this execution, not just what the interceptor generally does. Context matters.

#### 9. **VSCode Security - Scope Auto-Approval Narrowly**
- **Problem**: `.vscode/settings.json` had `"&": true` in terminal auto-approve list, whitelisting shell command chaining operator
- **Risk**: Allows arbitrary command chains to execute without confirmation via Copilot terminal tool
- **Fix**: Remove broad permission, keep only specific safe commands (`.venv\\Scripts\\python.exe`)
- **Learning**: Terminal auto-approval settings should list specific safe executables, never generic shell operators (`&`, `|`, `;`, etc.)

### Implementation Impact Analysis

**Why These Issues Were Caught in PR Review, Not Implementation:**
1. **No npm install during implementation** - TypeScript compilation didn't run, so import errors invisible
2. **Tests never executed** - Written but not run against actual test runner
3. **Focus on feature completion** - Concentrated on acceptance criteria, not exhaustive validation
4. **Single-author review gap** - No peer review before Copilot PR review

**Process Improvements Needed:**
- Run `npm install` immediately after updating package.json
- Execute tests locally before pushing (add to pre-push hook?)
- Run TypeScript compilation (`npm run typecheck`) as part of local validation
- Treat Copilot PR review as first-pass peer review, not final check

### Technical Debt Addressed

✅ Test reliability improved - async assertions, proper mocking
✅ Documentation readability fixed - pure Markdown
✅ Configuration validation now functional
✅ Security tightened - removed broad terminal permissions
✅ Type safety improved - proper imports, no unused variables

**Remaining Known Issues:**
- Tests still require `npm install` to run (dependency installation not automated in workflow yet)
- Frontend test execution not integrated into main test suite (separate command)
- Pre-commit hooks not yet configured to enforce formatting/typechecks



## PR Review Process & Type Safety (Issue #4 - Review Implementation)

### Context
After implementing password hashing (Issue #4), received comprehensive code review feedback from GitHub Copilot PR Reviewer identifying 6 areas for improvement related to type safety, consistency, and test reliability.

### Key Learnings

#### 1. **TypedDict for Structured Return Types**
- **Problem**: Returning untyped `dict[str, str | int | list[str]]` from `calculate_password_strength()` made it impossible for type checkers to verify field names and types
- **Solution**: Created `PasswordStrengthResult` TypedDict with explicit fields (`score: int`, `strength: str`, `suggestions: list[str]`, `meets_policy: bool`)
- **Why it matters**: 
  - Enables static type checking at call sites
  - Prevents runtime KeyErrors from typos
  - Self-documenting API contract
  - FastAPI can validate response models against TypedDict structure
- **Learning**: Use TypedDict over generic dict for any structured data returned by functions

#### 2. **Consistency in Validation Logic**
- **Problem**: Special character regex differed between scoring (`has_special`) and policy validation (`validate_password_strength`), causing inconsistent user feedback
  - Scoring accepted: `[!@#$%^&*(),.?\":{}|<>\-_+=\[\]\\;'/~`]`
  - Policy accepted: `[!@#$%^&*(),.?\":{}|<>]`
  - Example: Underscore `_` counted toward strength score but failed policy check
- **Solution**: Extracted `SPECIAL_CHARS_PATTERN` constant, used in both functions
- **Learning**: When multiple functions validate the same concept, share validation logic through constants/helpers to ensure consistency

#### 3. **Safe TypedDict Unpacking with Pydantic**
- **Problem**: Router manually indexed dict fields (`result["score"]`, `result["strength"]`, etc.) which type checkers couldn't verify
- **Solution**: Changed from manual construction to `PasswordStrengthResponse(**result)` 
- **Why it works**: 
  - TypedDict structure matches Pydantic model fields exactly
  - Pydantic validates all required fields are present
  - Type-safe unpacking with runtime validation
  - Cleaner, more maintainable code
- **Learning**: When a TypedDict maps to a Pydantic model, use `**dict` unpacking to leverage Pydantic's validation

#### 4. **passlib `resolve` Parameter Behavior**
- **Problem**: `pwd_context.identify(hash, resolve=True)` returned handler object (class instance) instead of scheme name string
- **Solution**: Changed to `resolve=False` to get scheme name as string ("bcrypt")
- **Why it matters**:
  - Handler objects are not JSON-serializable
  - Inconsistent with documented return type (`scheme: str`)
  - Could cause runtime errors when serializing response
- **Learning**: Always verify library parameter behavior - `resolve=True` is for internal use, `resolve=False` for public API

#### 5. **Test Completeness - Asserting All Variables**
- **Problem**: Test defined `expected_min_strength` variable but never asserted it, allowing strength labeling bugs to slip through
- **Root Cause**: Test was written incrementally, assertion forgotten after adding parameter
- **Solution**: Added missing assertion `assert data["strength"] == expected_min_strength`
- **Impact**: Revealed that test expectations were incorrect (see #6)
- **Learning**: Review test parameters - if a variable is in the test data, it should be verified somewhere

#### 6. **Performance Test Reliability on CI**
- **Problem**: Single-run performance tests (`< 500ms`) were flaky on shared CI runners due to CPU load variance
- **Solution**: 
  - Use `time.perf_counter()` instead of `time.time()` (higher precision, monotonic)
  - Average across 3 iterations to smooth out variance
  - Relaxed threshold to 600ms (with 500ms target documented) for CI tolerance
- **Why it works**:
  - `perf_counter()` measures CPU time, not wall time
  - Averaging reduces impact of single slow run
  - Slightly relaxed threshold prevents CI flakiness while maintaining performance validation
- **Learning**: Performance tests need statistical approaches (averaging, percentiles) to handle CI runner variance

#### 7. **Password Strength Scoring Side Effect**
- **Discovery**: When aligning special character validation, test expectations revealed scoring algorithm produces higher scores than anticipated
  - "Test1!" (6 chars) scores 72 points → "strong" (not "weak" as expected)
  - Reason: Character variety (40pts) + complexity (20pts) + length (12pts) = 72pts
- **Analysis**: 
  - Short passwords can score "strong" if they have high variety/complexity
  - This may or may not be desired behavior (design decision)
  - Tests revealed this only after adding missing assertions
- **Learning**: Test assertions reveal algorithm behavior - use this to validate if implementation matches intent

### Process Learnings

#### When to Create TypedDict vs. Pydantic Model
- **TypedDict**: Internal function return types, not exposed to API
- **Pydantic Model**: Request/Response schemas, database models, API contracts
- **Both**: Use TypedDict internally, then validate/convert to Pydantic for API boundary

#### Code Review Value Beyond Bugs
- Type safety improvements don't change behavior but prevent future bugs
- Consistency issues (like special char mismatch) can cause confusing UX
- Test improvements (missing assertions, flakiness) improve CI reliability
- All 6 review items were valid despite tests passing initially

#### Why These Issues Weren't Caught Initially
1. **Type Safety**: Python's dynamic typing allows dict access without validation
2. **Consistency**: Both implementations worked independently, mismatch only visible in edge cases
3. **Test Coverage**: Tests passed because assertions were incomplete
4. **Performance**: Tests ran on fast developer machine, not CI

### Implementation Stats
- **Files Modified**: 4 (validators.py, router.py, password.py, 2 test files)
- **Changes**: ~50 lines modified/added
- **Test Results**: 108/108 tests passing, 90% coverage maintained
- **Review Suggestions**: 6/6 implemented
- **Time to Implement**: ~30 minutes

## Studienarbeit Analyse & PDF-Extraktion

### Context
Jana Bode's Studienarbeit "Entwicklung eines Prototyps für einen Nano-Marktplatz" (Januar 2025) dokumentiert die prototypische Umsetzung eines Marketplace-Systems für Nano-Learning-Einheiten im Projekt DiWeiWei.

### Key Learnings

#### 1. **Nano-Konzept & Learning-Modell**
- **Nano-Einheiten**: Kurze, in sich geschlossene digitale Lerneinheiten mit klarer thematischer Abgrenzung
- **Kompetenzstufen**: 3 Ebenen (Foundation/Intermediate/Advanced) definieren Lerntiefe
- **Module & Schulungen**: Nanos kombinieren zu Modulen, Module zu Schulungen für ganzheitliche Themenbereiche
- **Learning**: Modularer Aufbau ermöglicht adaptive, selbstbestimmte Lernpfade

#### 2. **Marketplace-Architektur (Studienarbeit vs. Production)**

**Prototype (Study)**:
- Python 3.13.1 mit Solara Framework (Full-Stack)
- MySQL mit XamPP für lokale Entwicklung
- **SICHERHEITSLÜCKEN IDENTIFIZIERT**:
  - ❌ Keine Password-Hashing (KRITISCH)
  - ❌ Kein TLS für Chat-Nachrichten
  - ❌ Keine DSGVO-Implementierung
  - ❌ Keine SQL-Injection-Protection
  - ❌ Chat via HTTP-Polling, nicht WebSocket

**Production Plan**:
- FastAPI Backend (statt Solara)
- PostgreSQL Aurora RDS (statt MySQL) → Gewählt wegen:
  - JSONB für flexible Datenstrukturen
  - German Full-Text-Search (FTS)
  - Superior ACID-Garantien
  - Bessere Indexing-Optionen
- AWS Cloud-Native: ECS, RDS, S3, ElastiCache, Elasticsearch

#### 3. **Business Model: Tausch vs. Kaufmodell**

**Evaluated Concepts**:
1. Fixed-Price (wie Amazon) → ❌ Keine Interaktion
2. Negotiable-Price (wie Klein-Anzeigen) → ⚠️ Indirekte Kommunikation
3. **Barter Model** (GEWÄHLT) ✅:
   - Nanos werden OHNE festen Preis hochgeladen
   - Direkter Chat zwischen Creator und Consumer
   - Nanos werden getauscht (z.B. mein Nano für dein Nano)
   - **Learning**: Kommunikation > Transaktion für regionalen Marketplace

#### 4. **Anforderungen-Extraktion: 99+ Requirements**

**Kategorisiert als**:
- MUSS (27): Must-have features (Login, Upload, Search, Quality Controls)
- SOLL (35): Should-have features (Ratings, Comments, Moderation)
- KANN (37): Nice-to-have features (AI recommendations, Analytics)

**Professionalisierungs-Gaps Identifiziert**:
- 23 Security/Compliance Requirements missing in Prototype
- Moderation Workflow nicht implementiert
- DSGVO Data Export/Anonymization fehlt
- 2FA/Password-Strength nicht vorhanden

#### 5. **Domain Model & Data Normalization**

**11 Core Entities**:
1. USER → 6 attributes + roles (Creator, Consumer, Admin, Moderator)
2. ORGANIZATION → Multi-Org support (Phase 1)
3. NANO → Content unit (18 attributes: title, duration, status, file_path, license, etc.)
4. NANO_VERSION → Immutable versioning
5. NANO_CATEGORY_ASSIGNMENT → N:M relationship (max 5 per nano)
6. RATING → 1-5 star system
7. CHAT_SESSION & CHAT_MESSAGE → Encryption ready
8. FAVORITE & SAVED_LIST → User personalization
9. AUDIT_LOG → DSGVO compliance (7-year retention)
10. MODERATION_FLAG → Content review workflow

**Normalization Decision**: 3NF with strategic denormalization:
- `average_rating` cached (trigger-based updates)
- `download_count` aggregated nightly
- **Why**: Performance optimization vs. query complexity trade-off

#### 6. **Architecture Pattern: Monolith → Microservices**

**MVP Decision**: Modular Monolith (not premature microservices)
- **8-week sprint** demands tight coupling
- **150 PT sustainability** limit
- **10 well-defined modules** enable clean service extraction later

**Modules**:
1. Identity & Auth (JWT, 2FA)
2. Nano Catalog (Upload, CRUD, Versioning)
3. Search & Discovery (FTS, Faceting)
4. Feedback (Ratings, Comments, Moderation)
5. Messaging (Chat, Encryption)
6. Profiles & Organizations
7. Favorites & Lists
8. Moderation & Abuse
9. Audit & DSGVO
10. Analytics

**Phase 2 Migration Path**:
- Auth → Keycloak microservice
- Chat → Node.js (WebSocket native)
- Search → Elasticsearch cluster
- Keep Content & Profiles in monolith initially

#### 7. **Technology Stack Decisions**

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Backend Framework** | FastAPI | Async, type-safe, auto-docs, AWS-ready |
| **Frontend** | React 18+ | Industry standard, component reusability |
| **Database Primary** | PostgreSQL Aurora | JSONB, FTS, ACID, AWS RDS managed |
| **Search Engine** | AWS OpenSearch | German tokenizer, faceting, managed |
| **Object Storage** | S3 | Nano ZIPs, avatars, immutable audit logs |
| **Session Cache** | ElastiCache (Redis) | HttpOnly cookies, 30-60min TTL |
| **Infrastructure** | AWS ECS + ALB | Load balancing, auto-scaling, managed |
| **Real-time Chat** | Polling (MVP) → WebSocket Phase 1 | Simplified MVP, upgrade path clear |

#### 8. **DSGVO Implementation Strategy**

**Articles Mapped**:
- Art. 6 (Lawfulness) → Consent banner + purpose limitation
- Art. 12-22 (Data Subject Rights):
  - **Art. 15**: Data export via "Meine Daten" button → JSON/CSV
  - **Art. 17**: Right to erasure → Soft-delete with pseudonymization
  - **Art. 20**: Data portability → CSV export format standardized
  - **Art. 21**: Opt-out → Newsletter unsubscribe + communication preferences
- **Retention**: Audit logs 7-year (DSGVO + tax law)
- **Pre-Launch Gates**: 
  - ✓ Security audit passed
  - ✓ DSGVO audit passed
  - ✓ Penetration test passed

#### 9. **Risk Profile & Mitigations**

**Critical Risks**:
1. DSGVO Violation (40% prob) → Pre-launch legal audit
2. Chat Privacy Leak (35% prob) → TLS MVP, E2E Phase 2
3. Data Breach (20% prob) → AWS KMS, audit logging, incident runbook
4. SQL Injection (15% prob) → ORM (SQLAlchemy), prepared statements

**Business Risks**:
- Marketplace Coldstart (70% prob) → Seed content + early access program
- Creator/Consumer Imbalance (60% prob) → Asymmetric launch strategy
- Moderation Overhead (50% prob) → AI content filter Phase 1

#### 10. **MVP Scope & Budget**

**8-Week Sprint, 150 PT, 180k€**:
- 7 Epics: Auth (2w), Nanos (3w), Search (2w), Feedback (1w), Chat (1w), Moderation (1w), DevOps (2w, parallel)
- Team: 1 Senior Dev + 1 Full-Stack + 0.5 DevOps + 0.5 QA + 1 PM (5 FTE)
- Go-Live Target: Q3 2025
- Post-MVP: 180k€/year for scaling

#### 11. **Testing Strategy: Pyramid Approach**

**Coverage Targets**:
- **Unit** (70%): Password hashing, JWT validation, search ranking
- **Integration** (15%): API→Service→Repo, mocked DB fixtures
- **E2E** (5%): Playwright/Selenium, staging environment
- **Security** (10%): OWASP Top 10, DSGVO compliance, penetration testing
- **Performance** (Locust): 1000 concurrent users, p95 <1s latency

**CI/CD**: GitHub Actions with lint (flake8), test (pytest), security (SonarQube) gates

#### 12. **Deployment & Operations**

**Monitoring Stack**:
- CloudWatch (metrics), CloudWatch Logs (structured JSON), X-Ray (traces), SNS (alerts)
- **SLOs**: 99.95% uptime, p95 <1s latency, 5xx <0.5%
- **Capacity**: 1k DAU = 2 ECS tasks, 5k DAU = 3-4 tasks, 10k DAU = 5-8 tasks

**Incident Response**: SEV-1 (page on-call), SEV-2 (normal response), post-mortem 24h

**Backup/DR**: RTO <1h, RPO <15min, monthly DR drills

#### 13. **Architectural Decisions (9 ADRs)**

**Key Decisions**:
- ADR-001: Monolith (MVP speed) vs Microservices (later)
- ADR-002: PostgreSQL (FTS, JSONB) vs MySQL (simplicity)
- ADR-003: React (market fit) vs Vue (lighter)
- ADR-004: JWT+Refresh (stateless) vs Database sessions
- ADR-005: S3 (scalable) vs BLOB (simpler)
- ADR-006: Elasticsearch (rich queries) vs DB full-text
- ADR-007: Polling (MVP) vs WebSocket (Phase 1)
- ADR-008: Payment (defer Phase 2) vs Tausch-model MVP
- ADR-009: Chat TLS (MVP) vs E2E (Phase 2)

#### 14. **PDF Extraction & Study Integration**

**Process**:
1. PDF Study (114 pages) → pdfplumber extraction
2. Structured analysis → 570-line detailed document
3. Requirements professionalization → 99 mapped requirements
4. Planning documents → 13-file suite covering all aspects

**Learning**: Programmatic PDF extraction enables systematic requirements capture from academic research.

#### 15. **Professionalization Vectors**

**Gap Analysis - Prototype → Production**:

| Area | Prototype | Production |
|------|-----------|-----------|
| Password Storage | ❌ Plain text | ✓ Argon2 (12 rounds) |
| Chat Encryption | ❌ HTTP polling | ✓ TLS MVP, E2E Phase 1 |
| DSGVO | ❌ None | ✓ Art. 6, 12-22, 21 |
| SQL Injection | ❌ No protection | ✓ ORM + Prepared statements |
| Moderation | ❌ Comments only | ✓ Review workflow + flags |
| Monitoring | ❌ Console logs | ✓ CloudWatch + SLOs |
| Testing | ❌ Manual | ✓ 80%+ coverage + CI/CD |
| Deployment | ❌ Local XamPP | ✓ AWS ECS multi-AZ |
| Scalability | ❌ Single machine | ✓ Auto-scaling 1-10k DAU |
| Audit Trail | ❌ None | ✓ Immutable 7-year retention |

---

## Meta-Learnings for Future Projects

1. **Prototype-to-Production Gap**: Academic prototypes require 15-20x effort for production hardening
2. **Modularity Early**: Defining 10 modules in MVP enables cleaner Phase 2 microservice migration
3. **PDF as Requirements Source**: Systematic PDF analysis beats manual reading; enables requirements traceability
4. **Regional Marketplace Dynamics**: Barter models suit B2B regional ecosystems; eCommerce patterns don't translate directly
5. **Security is Foundational**: Plan DSGVO/encryption architecturally; retrofitting is exponentially harder

---

## Story 1.1: User Registration & Login Implementation (2026-02-27)

### Architecture Decisions & Rationale

#### 1. **FastAPI + Async SQLAlchemy Choice**
- **Decision**: FastAPI (async) over Django for green-field project
- **Rationale**: 
  - Native async/await support aligns with modern Python (3.13.1)
  - Better resource utilization under load (important for 1k-10k DAU target)
  - Simpler learning curve for team vs Django ORM
- **Trade-off**: Less mature ecosystem, but well-documented for auth patterns
- **Outcome**: 87% code coverage achieved with 37 comprehensive tests

#### 2. **Pydantic V2 BaseSettings with ConfigDict**
- **Decision**: Migrated from deprecated `class Config` pattern immediately
- **Learning**: Pydantic V2 forces cleaner config management early
- **Impact**: Zero deprecation warnings, future-proof for Pydantic 3.x
- **Optimization**: ConfigDict({env_file='.env'}) enables environment-driven config without hardcoded defaults

#### 3. **Password Hashing: Bcrypt + PBKDF2 Fallback**
- **Problem**: Bcrypt backend failure on Windows during development
- **Solution**: Implemented dual-mode hashing
  - Primary: Bcrypt (industry standard, slow-by-design)
  - Fallback: PBKDF2-HMAC-SHA256 (for development/CI environments)
- **Learning**: Infrastructure variance (Windows vs Linux) should be handled transitively, not rejected
- **Security Note**: Same password verification logic works for both, no weakening

#### 4. **Account Lockout: Timestamp-Awareness Issue**
- **Problem**: SQLite test database returns naive datetimes; production (PostgreSQL) returns aware datetimes
- **Solution**: Defensive comparison with tzinfo detection and normalization
- **Code Pattern**: Type-aware timezone handling prevents runtime errors
- **Learning**: TestClient (sync) + SQLAlchemy async requires careful fixture scoping
- **Outcome**: All 37 tests pass with SQLite; production behavior validated

#### 5. **JWT Token Split: Access (15min) + Refresh (7day)**
- **Design**: Dual-token strategy reduces exposure window
- **Rationale**:
  - Access token (short-lived) sent with every request - lower damage if compromised
  - Refresh token (long-lived) stored securely - enables "remember me" UX
  - Refresh endpoint allows token rotation without re-authentication
- **Alternative Considered**: Single JWT (simpler) → rejected for security
- **Implementation**: Separate token creation functions for flexibility

#### 6. **Email Verification: Flag-Based vs Token-Based**
- **Implemented**: Flag-based (email_verified boolean) for MVP
- **Future**: Token-based verification with email sending
- **Learning**: MVP focuses on logic validation; email infrastructure separated
- **Rationale**: Enables offline testing; matches 24h token requirement from issue

### Testing Insights

#### Test Pyramid Architecture
- Route Tests (17): HTTP status codes, request/response formats
- Service Tests (20): Business logic, validation, state changes

#### Fixture Design Lessons
- **db_session Lifecycle**: Function-scoped (per-test) prevents data pollution
- **TestClient Integration**: Synchronous client with async routes requires proper dependency override
- **Shared Session Pattern**: Multiple HTTP requests within one test share db_session for state verification
- **expire_on_commit=False**: Critical for detecting state changes across requests

#### Coverage Analysis
- **High Coverage (94-100%)**: Core logic, models, schemas
- **Adequate Coverage (61-68%)**: Error paths, edge cases (validators, password fallback)
- **Insight**: 87% total coverage with 37 tests is sustainable; further gains require diminishing effort

### Data Model Decisions

#### User Entity Fields (Production-Ready)
- Authentication: email (unique, case-insensitive), username (unique), password_hash
- Status & Security: status enum, role enum, login_attempts counter, locked_until timestamp
- Account Lifecycle: created_at, updated_at, last_login, email_verified flag, verified_at timestamp
- **Learning**: Modeled for future features without future schema migration
- **Security**: Immutable user IDs (UUID); no PII in URLs or logs

### Validation Strategy Layering

| Layer | Technology | Examples |
|-------|-----------|----------|
| Schema | Pydantic V2 | min_length, pattern regex, EmailStr |
| Business | Custom validators | Password strength, username format |
| Database | SQLAlchemy constraints | Unique indexes |
| Application | Service layer | Duplicate checks, account state |

- **Learning**: Each layer serves different purpose; no duplication
- **Testing**: Pydantic errors (422) vs business errors (400/409/401/403) require distinct test cases

### Review Learnings (PR Feedback)
- **Fail Fast on Secrets**: Enforce `SECRET_KEY` for production to avoid insecure defaults.
- **JWT Claim Validation**: Defensive claim parsing prevents 500s on malformed tokens.
- **CORS Safety Defaults**: Avoid wildcard origins with credentialed requests.
- **Repository Hygiene**: Keep machine-specific editor settings out of source control.

---

## Meta-Learnings: Story 1.1 Implementation

1. **Async-from-Day-One**: Starting with async/await pays off when TestClient test coverage reaches 100%
2. **Config as First-Class**: Environment-driven config prevents "works on my machine" syndrome
3. **Defensive Programming**: Timezone/encoding/backend assumptions should be validated, not asserted
4. **Test Isolation**: Function-scoped fixtures + fresh database per test prevents hours of debugging
5. **Security Patterns**: Account lockout, JWT split tokens, password hashing should be copyable templates

---

**Document Updated**: 2026-02-27
**Status**: Story 1.1 Complete (87% coverage, 63/63 tests) → Issues #10-#13 Complete

---

## Bugfix Learnings: Issue #8 (Register endpoint DB outage handling)

- **Graceful Degradation for Infrastructure Errors**: DB connection failures during request handling must be translated to stable API responses (e.g. 503) instead of leaking internal stack traces via unhandled 500 errors.
- **Boundary-Level Exception Mapping**: For FastAPI modular design, mapping infrastructure exceptions at the route boundary keeps service logic focused and preserves a consistent external error contract.

---

## PR #15 Review Process Learnings: GitHub API vs UI Discrepancy

**Issue**: Copilot AI review comments on PR #15 did not appear in `github-pull-request_issue_fetch` API response (comments array was empty), but were clearly visible in GitHub UI screenshot showing a comment on `app/modules/auth/middleware.py` lines 99-101.

**Root Cause**: GitHub's GraphQL/REST APIs may not consistently return all review comments in the general `comments` array. Review comments are stored separately from PR comments and require specific GraphQL queries or REST endpoints to retrieve.

**Solution**: 
1. **Enhanced nano_review.prompt.md**: Added guidance to manually inspect PR UI or use alternative data sources when API fetch returns incomplete comments.
2. **Typing Best Practice Discovered**: The Copilot suggestion to add return type annotation to dependency factories (`require_role`) reveals a gap - FastAPI dependency factories should be fully typed using `Callable[[...], Awaitable[...]]` for IDE tooling and type checking.

**Implementation Fix**:
- Added `Callable` and `Awaitable` imports from `collections.abc` and `typing`
- Annotated `require_role(required_role: str) -> Callable[[Annotated[TokenData, Depends(get_current_user)]], Awaitable[TokenData]]`
- Benefit: Full type coverage enables FastAPI/IDE to provide better autocomplete and catch type errors earlier

**Meta-Learning**: When automating PR review implementation, use multiple data sources:
1. Structured API responses (fast but may be incomplete)
2. Visual UI inspection (slow but authoritative - what user actually sees)
3. Fallback to manual comment collection when mismatch detected

This prevents missing reviewer feedback that could affect code quality.
- **Regression Test Shape**: Route-level monkeypatching of `register_user` to raise `OperationalError` is a fast and deterministic way to lock in behavior for dependency outages without requiring real DB/network failures.
- **Documentation Alignment**: Error response changes should be reflected in endpoint docs (`README` and OpenAPI response metadata) to keep client expectations synchronized with runtime behavior.

### Review Follow-up Learnings (PR #9)

- **Exception Scope Precision**: Broad exception handlers (`OSError`) can hide unrelated bugs and create false infrastructure signals. Map only DB-specific exceptions at HTTP boundaries.
- **Negative Regression Coverage**: Add explicit guard tests for non-targeted exceptions to ensure future refactors do not accidentally broaden error translation behavior.
- **Typed Test Doubles**: Monkeypatched async test doubles should have explicit parameter and return typing to keep test code maintainable and consistent with strict typing standards.

## Feature Learnings: Issue #10 (Docker Integration Tests)

- **Docker Compose for Local Testing**: Multi-container orchestration enables realistic integration testing without mocking. PostgreSQL 13 Alpine on port 5433 (non-standard) avoids local Postgres conflicts.
- **Test Markers for Environment Separation**: `@pytest.mark.integration` vs `@pytest.mark.unit` allows unified test suite with flexible execution (`pytest -m unit` for fast local runs, `-m integration` for Docker verification).
- **Async Test Fixtures with PostgreSQL**: AsyncSession + async_sessionmaker with PostgreSQL requires connection pooling awareness - test isolation is managed by pytest fixtures, not transactions (transactions don't rollback in async context).
- **GitHub Actions CI/CD Pipelining**: Separate `unit-tests` and `integration-tests` jobs prevent Docker dependency failures from blocking fast unit test feedback - Docker-less jobs run in seconds.
- **Health Checks in Compose**: `healthcheck.test: ["CMD", "pg_isready", ...]` ensures dependency readiness before tests start - eliminates race conditions during container startup.

## Configuration Learnings: Issue #11 (Database Connection Configuration)

- **Environment Variable Priority**: Implement tiered detection: `TEST_DB_URL` (override) > `DATABASE_URL` (explicit) > defaults (fallback). This enables seamless environment switching without code changes.
- **Driver Dialect Conversion**: PostgreSQL requires explicit asyncpg driver specification: `postgresql://` → `postgresql+asyncpg://` at runtime. This conversion in config layer prevents repeated driver selection logic.
- **Connection Validation at Startup**: Initialize engine with `.connect()` before app startup to fail fast on misconfiguration rather than at first request. Includes validating driver availability.
- **Error Messages as Documentation**: Connection errors should hint at solutions: "Database URL not set. Set DATABASE_URL or TEST_DB_URL environment variables" guides users to proper configuration without debugging.
- **Async Driver Specificity**: asyncpg and aiosqlite are required (not psycopg2 or sqlite3) - synchronous drivers block the event loop. Type hints and runtime checks prevent accidental synchronous driver usage.

## Infrastructure Learnings: Issue #12 (Database Schema Initialization)

- **Standalone Initialization Scripts**: `scripts/init_db.py` enables one-command schema setup (`python scripts/init_db.py`) without running the full application, solving cold-start problems for new environments.
- **SQLAlchemy Base.metadata Automation**: Reflecting models into DDL via `Base.metadata.create_all()` eliminates manual schema maintenance. Models and schema stay synchronized naturally.
- **Multiple Initialization Pathways**: Document 4 options (script, registration trigger, Alembic, manual SQL) - different users prefer different approaches. Script is fastest for development; Alembic is best for migrations.
- **Idempotent Initialization**: `create_all()` is idempotent (safe to call multiple times), but consider adding `IF NOT EXISTS` guards for production safety and clearer intent.
- **Initialization Documentation**: Schema errors like "relation does not exist" indicate missing initialization step. Prominent README section prevents user confusion and support overhead.

## Feature Learnings: Issue #13 (Email Verification Implementation)

- **JWT Tokens for Stateless Verification**: Email verification tokens as JWT (instead of database tokens) eliminate token storage and lookup overhead. Token expiration embedded in `exp` claim - no cleanup jobs needed.
- **Token Type Discriminator**: Including `"type": "email_verification"` in JWT payload allows reusing `verify_token()` function for multiple token types (access/refresh/email) with explicit type checking. Prevents token substitution attacks.
- **24-Hour Token Expiry Sweet Spot**: Long enough for users to receive and process email, short enough to limit token abuse window. Configurable via `EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS` for flexibility.
- **Service Layer Abstraction**: `verify_email_with_token()` and `resend_email_verification_token()` are testable, reusable service functions. HTTP-specific concerns (error handling, response codes) stay in router layer.
- **Comprehensive Integration Fixtures**: `verified_user` fixture creates and verifies a test user in one call, reducing test boilerplate and ensuring consistent test state. Reduces test code from 5 lines to 1 parameter.
- **MVP Email MVP**: Returning token in API response (instead of sending email) enables complete endpoint testing without SMTP dependency. Clear documentation marks this as MVP; production path (email service integration) is defined.
- **Test Coverage Strategy**: 16 dedicated email verification tests cover: token generation, validation, expiration, endpoint success/failure, edge cases (already verified, non-existent user), and end-to-end flow. Tests are integration tests (use real DB).
- **Error Messaging for Users**: "Invalid or expired email verification token" is clear and actionable. Errors don't leak token internals or expose timing vulnerabilities.
- **Login Flow Integration**: Email verification is enforced at authentication time (403 Forbidden if not verified). This creates natural verification incentive - users must verify to access the system.

## Testing Learnings: All Issues

- **Coverage Target 87%**: Exceeds 70% requirement while staying under "over-testing" point (99%). Focus on business logic and error paths, skip trivial getter/setter coverage.
- **Pytest Async Patterns**: Use `async def` test functions with `@pytest.mark.asyncio`. AsyncSession + SQLAlchemy 2.0 async driver handles connection pooling per test safely.
- **Fixture Scope Management**: Session-scoped engine (created once per test session), function-scoped session (fresh per test) prevents cross-test pollution while minimizing setup time.
- **Docker Compose Test Environment**: PostgreSQL in Docker provides realistic integration testing without local Postgres installation. Tests can validate constraints, triggers, and dialect-specific behavior (JSONB, FTS).
- **Monkeypatching for Dependency Injection**: When integration tests aren't feasible, monkeypatch service functions to simulate failures (OperationalError, missing data). Faster than Docker-based tests but less realistic.
- **Black + isort Enforcement**: Automatic formatting removes style discussions from code review. `black --check` + `isort --check` in CI ensures consistency without manual intervention.

## Project Health Indicators

| Metric | Issue Resolution | Result |
|--------|------------------|--------|
| Test Coverage | #10 Docker tests | 87.18% (target 70%) ✅ |
| Test Count | #13 Email verification | 63 tests (was 47) ✅ |
| Configuration | #11 Environment setup | TEST_DB_URL priority logic ✅ |
| Schema Init | #12 Database setup | 4 initialization methods documented ✅ |
| Documentation | All issues | README, IMPLEMENTATION_STATUS updated ✅ |
| Code Quality | All issues | Black + isort + pytest passing ✅ |

**Key Achievement**: Transitioned from manual testing (SQLite only) to automated Docker integration tests + unit tests. Project now validates behavior on production-compatible PostgreSQL at CI time.

## Review Learnings: PR #18 (Copilot Review Follow-up)

- **Auth Semantics Must Match API Contracts**: `HTTPBearer()` defaults to 403 when the header is missing. For endpoints documented as 401 on missing/invalid token, use `HTTPBearer(auto_error=False)` and raise explicit 401 in middleware.
- **OpenAPI Responses Must Mirror Runtime Errors**: If route handlers catch `OperationalError` and return 503, every affected endpoint should declare a 503 response in metadata to keep docs and client generation accurate.
- **Timezone Consistency in Schemas Matters**: Default timestamp fields in Pydantic schemas should use UTC-aware values (`datetime.now(timezone.utc)`) to avoid naive/aware mismatch issues.
- **Deletion Grace Period Needs Recoverability**: If account status is set to `INACTIVE` during deletion scheduling, auth/refresh rules must still allow access during the grace period so users can call cancellation endpoints.
- **Domain Errors Need Precise HTTP Mapping**: Shared exception types (like `GDPRError`) should be mapped to specific status codes (e.g., 404 for "User not found", 400 for invalid operation state) to keep behavior predictable.
- **Referential Integrity for Audit Tables**: Audit entities should use explicit foreign keys (`ConsentAudit.user_id -> users.id`) to prevent orphan records and ensure safe cascades.

## Compliance Learnings: Issue #5 (GDPR Data Protection Implementation)

### Context
Story 1.4 required GDPR compliance basics: consent tracking, data export, account deletion with grace period. Implementation touched authentication flow, database schema, and API layer.

### Technical Learnings

1. **Consent as First-Class Citizen**
  - Consent isn't just a checkbox, it's an audit trail requirement
  - Every consent decision needs: timestamp, type, user_id, acceptance status
  - Registration-time consent stored in User model + ConsentAudit table
  - **Pattern**: User model holds current state, ConsentAudit holds history
  - **Why**: Supports GDPR Article 7 (demonstrable consent) and Article 30 (records of processing)

2. **Schema Design: Boolean vs. Timestamp for Consent**
  - **Rejected**: `accepted_terms: bool` (no proof of when consent was given)
  - **Chosen**: `accepted_terms: datetime` (timestamp = acceptance proof)
  - **Learning**: GDPR audits require demonstrable consent with date/time
  - ConsentAudit table provides full consent lifecycle history

3. **Right to be Forgotten: Soft vs. Hard Delete**
  - **Grace Period Pattern**: 30-day window allows accidental deletion recovery
  - `deletion_requested_at`: timestamp when user requested deletion
  - `deletion_scheduled_at`: calculated as `requested_at + 30 days`
  - During grace period: account deactivated (status = INACTIVE)
  - After grace period: permanent hard delete of user + consent records
  - **Learning**: GDPR Article 17 requires deletion, but user experience demands grace period

4. **Timezone Handling Across SQLite/PostgreSQL**
  - SQLite stores datetime without timezone info (naive datetime)
  - PostgreSQL stores timezone-aware datetime (TIMESTAMP WITH TIME ZONE)
  - **Problem**: Comparing naive datetime to aware datetime raises exception
  - **Solution**: Defensive datetime comparison in `execute_account_deletion()`:
    ```python
    now_utc = datetime.now(timezone.utc)
    scheduled = user.deletion_scheduled_at
    if scheduled.tzinfo is None:
      scheduled = scheduled.replace(tzinfo=timezone.utc)
    if now_utc < scheduled:
      return False  # Grace period not expired
    ```
  - **Learning**: Always assume datetime may be naive in cross-database code

5. **Test Fixtures Cascade: Global vs. Local Consent**
  - Initial implementation: `UserRegister` added `accept_terms` and `accept_privacy` required fields
  - **Problem**: 65+ existing tests failed due to missing consent in fixture
  - **Solution**: Updated `conftest.py` global `test_user_data` fixture with consent fields
  - **Learning**: Schema changes ripple through entire test suite—update global fixtures first
  - Alt pattern considered: Add `**kwargs` to allow optional fields → Rejected (explicit > implicit)

6. **Data Export Format: Human-Readable vs. Machine-Readable**
  - **GDPR Article 20**: Right to data portability requires "structured, commonly used, machine-readable format"
  - **Chosen**: JSON with ISO 8601 timestamps
  - Export includes: user profile, consent timestamps, consent history
  - Future: Support CSV download for Excel compatibility
  - **Learning**: JSON satisfies legal requirement and enables automation

7. **API Design: GDPR Endpoints Follow RESTful Principles**
  - `GET /me/export` - Retrieve data (idempotent)
  - `GET /me/consents` - Retrieve consent history (idempotent) 
  - `POST /me/delete` - Initiate deletion (not idempotent—creates scheduled event)
  - `POST /me/cancel-deletion` - Cancel deletion (idempotent—same effect if called multiple times)
  - **Learning**: GDPR operations map cleanly to REST verbs when thoughtfully designed

### Workflow Learnings

1. **Prompt Interpretation: Literal vs. Inferred Instructions**
  - **Error**: Agent created feature branch when prompt said "switch TO main"
  - **Lesson**: nano_implement.prompt.md says "switch to main", NOT "create branch FROM main"
  - **Rule**: Do not add implied workflow steps that aren't in the prompt
  - **Context**: User corrected this, reinforcing importance of literal prompt interpretation

2. **Test Coverage Expectations**
  - 28 new GDPR tests added (14 service-level + 14 API-level)
  - Coverage increased from 86.97% → 94.01%
  - **Pattern**: Every service function gets test class, every endpoint gets API test
  - **Why**: GDPR is legally sensitive—comprehensive test coverage reduces compliance risk

3. **Documentation Updates Track Implementation**
  - IMPLEMENTATION_STATUS.md updated with Story 1.4 section
  - Acceptance criteria mapped to code locations for traceability
  - Test coverage summary shows GDPR contribution to overall test suite
  - **Learning**: Documentation isn't post-implementation task—it's completion validation

### Architecture Decisions

1. **ConsentAudit Table: Separate vs. Embedded**
  - **Rejected**: JSON field in User table for consent history
  - **Chosen**: Dedicated ConsentAudit table with foreign key to User
  - **Why**: Supports complex queries (e.g., "users who never accepted marketing consent")
  - Future: Enables consent withdrawal tracking (accepted=False entries)

2. **Grace Period Implementation: Application vs. Database**
  - **Rejected**: PostgreSQL scheduled job (pg_cron) to auto-delete after 30 days
  - **Chosen**: Application-level `execute_account_deletion()` function
  - **Why**: More portable (works with SQLite in tests), easier to test, explicit control
  - Production: Will be called by scheduled task (Celery beat or AWS EventBridge)

3. **Middleware Simplification**
  - Original middleware.py included Redis blacklist checking
  - GDPR implementation only needed JWT validation
  - **Decision**: Recreated simplified middleware with just authentication
  - **Learning**: MVP features may not need full production complexity

### Security Considerations

1. **Hard Delete = Permanent Data Loss**
  - After grace period, user and consent records are irrecoverably deleted
  - No soft delete flag (status=DELETED) used for RTBF
  - **Why**: GDPR Article 17 requires actual deletion, not just hiding data
  - **Risk**: Admin accidentally triggers deletion → Grace period provides safety net

2. **Authentication on GDPR Endpoints**
  - All GDPR endpoints require valid JWT token
  - `get_current_user_id()` dependency ensures user can only access own data
  - **Security**: Prevents data leakage via account enumeration
  - Future: Add rate limiting to prevent abuse (e.g., repeated export requests)

3. **Audit Trail Preservation**
  - ConsentAudit records deleted WITH user (CASCADE delete)
  - **Trade-off**: Compliance (delete all data) vs. Audit trail (keep consent history)
  - **Decision**: Full deletion wins for MVP
  - Production consideration: Anonymize instead of delete (replace PII with hash)

### Testing Patterns

1. **Email Verification Dependency**
  - Login requires verified email (from Story 1.1)
  - All API tests need `verify_user_email()` before login
  - **Error**: Initial tests forgot verification step → 401 Unauthorized
  - **Fix**: Added verification to all API test setup
  - **Learning**: Authentication dependencies propagate through integration tests

2. **Timezone Testing Strategy**
  - Tests use `datetime.now(timezone.utc)` explicitly
  - Mock time with `freezegun` for grace period expiration tests
  - **Pattern**: Test both naive and aware datetime scenarios
  - **Why**: Ensures code handles SQLite (naive) and PostgreSQL (aware) correctly

### Future Enhancements Identified

1. **Consent Versioning**: Track which version of Terms/Privacy Policy was accepted
2. **Email Notifications**: Send confirmation when deletion scheduled/cancelled
3. **IP + User-Agent Tracking**: Record where consent was given (audit requirement)
4. **Data Export Extensions**: Include related entities (transactions, content created)
5. **Automated Deletion Job**: Scheduled task to execute deletions after grace period
6. **Legal Document Management**: Admin interface to publish/update Terms & Privacy Policy

### Metrics Impact

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Test Count | 63 | 91 | +28 tests ✅ |
| Test Coverage | 86.97% | 94.01% | +7.04% ✅ |
| DB Tables | 9 | 10 | +1 (ConsentAudit) |
| API Endpoints | 6 | 10 | +4 GDPR endpoints |
| User Model Fields | 8 | 12 | +4 GDPR fields |
| Authentication Flow | Simple | Consent-validated | Registration now validates consent |

**Key Achievement**: Established GDPR compliance foundation covering 6 of 7 acceptance criteria. Project now has legally defensible consent tracking, data export, and right-to-be-forgotten mechanisms. Only missing production privacy policy document (requires legal review).
---

## Security Learnings: Issue #4 (Password Hashing Implementation)

- **Bcrypt Cost Factor Selection**: Cost factor 12 (2^12 = 4096 iterations) balances security against performance. OWASP recommends minimum 10; we chose 12 for future-proofing. Each increment doubles computation time - test on lowest-spec production hardware.
- **No Fallback Schemes for Production**: Initial implementation had pbkdf2 fallback for Windows compatibility. Removed in production version - fallbacks create security ambiguity and testing complexity. If bcrypt fails, fail fast with clear error rather than silently degrading security.
- **Long Password Handling**: Bcrypt has 72-byte limit. SHA256 pre-hashing for passwords >72 bytes prevents truncation while maintaining bcrypt benefits. Consistent pre-hashing application in both `hash_password()` and `verify_password()` is critical.
- **Constant-Time Comparison**: Passlib's `verify()` uses constant-time comparison internally to prevent timing attacks. Explicit documentation of this property important - developers might not realize security guarantees.
- **Password Strength Scoring Algorithm**: Multi-factor scoring (length 40pts, variety 40pts, complexity 20pts) provides nuanced feedback. Avoid binary "strong/weak" - users need actionable improvement path. Concrete suggestions ("Add uppercase letters") drive better outcomes than generic warnings.
- **Passwords Never in Logs**: Defensive programming with explicit checks: passwords excluded from log messages, error details, and exception arguments. Test with `caplog` fixture to verify no password leakage during failures.
- **API-Based Strength Checking**: Providing `POST /api/v1/auth/check-password-strength` endpoint enables real-time frontend feedback during registration. Critical: endpoint MUST NOT store or log passwords - stateless computation only.
- **Performance Testing for Security**: Hash/verify operations under 500ms requirement validates bcrypt cost factor choice. Performance tests catch configuration mistakes (e.g., accidentally setting cost=15 would exceed limits on low-end devices).
- **Hash Metadata Extraction**: `get_password_hash_info()` function enables migration planning - identify old hashes with lower cost factors for rehashing. Useful for security audits and compliance reporting.
- **Empty Password Validation**: Explicit ValueError for empty passwords prevents edge cases and provides clear error messages. Defense-in-depth: validation at schema level (pydantic), service level, and hashing level.
- **Length Limits for DoS Prevention**: Maximum password length (1000 chars) prevents denial-of-service via excessive computation. Bcrypt pre-hashing with SHA256 for long passwords + absolute limit creates two-layer defense.
- **Test Fixture Design for Passwords**: `client` fixture (synchronous TestClient) vs `async_client` fixture - password endpoint does not require async client. Incorrect fixture choice causes "can't await" errors.
- **Unicode Password Support**: UTF-8 encoded passwords work correctly with bcrypt. SHA256 pre-hashing for long UTF-8 passwords (emoji, Chinese, etc.) prevents byte-count surprises. Test with diverse Unicode character sets.
- **Common Pattern Detection**: Regex checks for "password", "123", "abc", "qwerty" patterns reduce score and trigger warnings. Balance between helpful guidance and over-constraining (don't reject all dictionary words - focus on extremely common patterns).
- **Strength Label Thresholds**: 5-tier system (weak/fair/good/strong/very_strong) with score cutoffs 20/40/60/80. Labels calibrated so compliant passwords (meets policy) start at "good" level, encouraging users toward "strong/very_strong".

### Security Best Practices Established
1. **No Plain-Text Storage**: Only bcrypt hashes in `users.password_hash` column
2. **Immediate Hashing**: Passwords hashed in service layer before persistence - never passed to repository/model layers in plain text
3. **Schema Exclusion**: `UserResponse` schema excludes `password_hash` - hashes never sent to frontend
4. **Verification Logging**: Failed login attempts logged (for rate limiting) but passwords excluded from logs
5. **Error Message Safety**: Authentication errors ("Invalid email or password") don't leak whether email exists or password was wrong
6. **Cost Factor Future-Proofing**: Bcrypt cost factor configurable via constant - enables security updates without code changes

### Testing Strategy for Security Features
- **Edge Case Coverage**: Empty passwords, very long passwords, special characters, Unicode, invalid hash formats
- **Performance Validation**: All operations <500ms on test hardware (prevents production surprises)
- **No Leakage Verification**: `caplog` fixture confirms passwords absent from log output during errors
- **Integration Flow Testing**: Complete registration→hash→store→verify→authenticate cycle validated end-to-end
- **Multiple User Same Password**: Verifies unique salts - same password produces different hashes
- **Strength Calculator Test Matrix**: 12 test scenarios covering scoring algorithm, suggestions, policy compliance, edge cases

### Implementation Metrics
- **Test Coverage**: 90% (45 password-specific tests added, total 108 tests)
- **New Code Lines**: ~300 lines (password.py enhancements + validators.py strength calculator + tests)
- **API Endpoints Added**: 1 (`POST /api/v1/auth/check-password-strength`)
- **Security Compliance**: OWASP password storage guidelines fully met

**Key Achievement**: Eliminated critical security vulnerability identified in prototype study - transitioned from no password hashing to production-grade bcrypt implementation with comprehensive testing and user-friendly strength feedback system.
## Learnings: Issue #3 JWT Token Management

- **JWT Claims Consistency**: Using both standard `sub` and legacy `user_id` claims preserves backward compatibility while aligning with JWT conventions. Adding `iat` and `role` improved downstream authorization checks and token auditability.
- **Refresh Token Rotation**: Rotation is most robust when old refresh tokens are both blacklisted and replaced atomically in Redis. This prevents replay in race conditions where clients retry stale refresh requests.
- **Redis as Token State Layer**: Stateless access tokens still need a stateful revocation channel. Redis key patterns (`refresh_token:{user_id}`, `blacklist:{token}`) with TTL-based expiry gave predictable cleanup and simple lookup semantics.
- **Middleware-Centric Validation**: Centralizing signature checks, expiry checks, and blacklist checks in auth middleware avoids duplicated endpoint logic and keeps protected-route behavior consistent.
- **Security/Data Minimization**: Tokens should contain only identity and authorization claims (`sub`, `email`, `role`, `iat`, `exp`, `type`), never password or secret-derived data.
- **Test Infrastructure Dependency**: Redis-backed auth tests are integration-sensitive; deterministic results require Redis availability during tests. This should be treated as part of the test environment contract, not as optional runtime state.

---

## Audit Logging Framework Implementation: Issue #6

### Context
Story 1.5 implemented comprehensive audit logging for tracking user actions, suspicious activity detection, and compliance. The implementation required solving cross-database compatibility issues, designing queryable audit schemas, and integrating logging into all authentication endpoints.

### Key Learnings

#### 1. **Cross-Database JSON Type Compatibility**
- **Problem**: Initial implementation used PostgreSQL-only `JSONB` type, causing "Compiler can't render element of type JSONB" error in SQLite test environment. Affected 140+ tests at collection phase.
- **Root Cause**: SQLAlchemy dialect system doesn't automatically translate JSONB to JSON for different databases - must be explicit
- **Solution**: Use `JSON().with_variant(JSONB, "postgresql")` pattern
- **Why it works**: `JSON()` is base type (SQLite-compatible), `.with_variant()` specifies dialect override, single codebase with no conditional logic
- **Learning**: Always use dialect-aware types for production-grade code. Test with multiple database backends or understand which types need variants.

#### 2. **Immutable Audit Trail Design**
- **Problem**: Initial consideration was audit log updates/deletions, but this conflicts with compliance requirements (tamper evidence)
- **Resolution**: Designed AuditLog as write-only (append-only) with only CREATE and DELETE (old entries only)
- **Why it matters**: Compliance requirement (tamper-evident), security (prevents covering up incidents), simplicity (no version tracking)
- **Learning**: Audit systems should be append-only. If deletion is needed, make it explicit and separate (retention cleanup).

#### 3. **Event Metadata Sanitization**
- **Problem**: Naive implementation might capture full request body (including passwords) in audit metadata
- **Resolution**: Explicit sanitization at source (endpoint level) - passwords, tokens NEVER captured
- **Example**: Pass only `{"email": user.email}` not full `request_body.dict()`
- **Learning**: Audit metadata sanitization is caller's responsibility, not logger's. Document what should NOT be logged.

#### 4. **Response Schema Field Mapping vs. Aliases**
- **Problem**: ORM has `event_data` field, but API should expose as `metadata`. Using alias with `populate_by_name=True` caused ambiguity
- **Solution**: Use direct field name in schema, map explicitly in router: `metadata=log.event_data`
- **Why it works**: Single, unambiguous field name, mapping at serialization time, no confusion about "correct" field name
- **Learning**: For ORM→API mapping, prefer explicit router mapping over schema aliases. Schema should reflect actual API response.

#### 5. **Pagination Limits for Performance**
- **Problem**: Without query limits, admin querying large audit table could cause memory/CPU overload
- **Solution**: Enforce maximum 1000 results per query with configuration: `limit = min(limit, 1000)`
- **Why it matters**: Cloud DB connections have memory limits, serializing millions of objects causes timeout, dashboard uses pagination naturally
- **Learning**: Add reasonable upper bounds to query limits. Document the limit and why it exists.

#### 6. **Suspicious Activity Detection with Time Windows**
- **Problem**: Brute force detection needs both COUNT (how many) and TIME (within what window)
- **Implementation**: Threshold-based with configurable window (default: 5 failures in 60 minutes)
- **Why it works**: 5 failures in 60 min = obvious attack, 5 in 30 days = user forgetting password, configurable thresholds adapt to policy
- **Learning**: For behavioral detection, always include time windows. COUNT without TIME is ambiguous.

#### 7. **Cross-Dialect Query Filter Handling**
- **Problem**: API receives action filter as string ("login_success") but service expects enum (AuditAction.LOGIN_SUCCESS)
- **Solution**: Graceful conversion with lenient fallback - ignore invalid action instead of returning 400
- **Trade-off**: Could be strict (400) or lenient (ignore). Chose lenient for dashboard resilience
- **Learning**: For enum filters, decide strictness upfront: strict vs lenient. Document the choice and reason.

#### 8. **Audit Log Integration Points**
- **Problem**: Deciding WHERE to add logging - too much noise, too little coverage, timing inconsistency
- **Solution**: Log at endpoint level, immediately after auth service calls complete, using a separate audit write/commit
  - `user = await register_user(db, ...)` → Business logic (service manages its own commit)
  - `await AuditLogger.log_action(db, ...)` → Log success in a follow-up operation
  - `await db.commit()` → Persist audit entry (not strictly atomic with auth service commit)
- **Why it works**: Logging synchronously in the request flow ensures coverage and observability, even though auth and audit changes use separate commits
- **Learning**: Audit logging should be synchronous and tightly coupled to core auth flows, but atomicity with business operations depends on transaction boundaries in the underlying services. Avoid async fire-and-forget systems for core audit paths.

#### 9. **Test Fixtures and Real Database Integration**
- **Problem**: Initial audit tests used non-existent fixtures (`db`, `user`, `auth_token`), causing collection-time failures
- **Root Cause**: Tests written before fixtures existed, used names from different test framework docs
- **Solution**: Use project's actual fixtures: `db_session`, `verified_user`, `async_client`
- **Discovery**: These fixtures already defined in conftest - no custom fixtures needed
- **Learning**: Use real fixtures for audit tests. Audit logging integration depends on real auth flows - mocking defeats the purpose.

#### 10. **Retention Cleanup for Compliance**
- **Problem**: Audit logs grow indefinitely, creating storage costs and compliance risk
- **Solution**: Configurable retention policy (default 90 days), cleanup called explicitly (not automatic)
- **Why 90 days**: Investigation window + compliance requirement + reasonable cost + PII retention principle
- **Implementation**: `cleanup_old_logs(retention_days=90)` - manual operation prevents accidental loss
- **Learning**: Make retention explicit and configurable. Document the reasoning. Don't make deletion automatic.

### Process Learnings

#### Database Schema Evolution for Multi-Database Support
- Single codebase for SQLite (test) + PostgreSQL (prod) requires `.with_variant()` planning upfront
- Integration tests with Docker PostgreSQL catch database-specific issues early
- Critical fix: One-line JSON type change resolved 140+ test failures - emphasizes catching dialect issues early

#### Audit Trail as System Documentation
- Well-designed audit logs become system documentation
- "Why was this user suspended?" → Check audit log for admin action + reason
- "Was there a security incident?" → Check suspicious activity detection results
- Audit logs serve business logic AND compliance AND security investigations

#### API Design for Operational Tools
- Audit API is operations-focused (admins querying logs), not user-facing
- Different constraints from user APIs: pagination limits for prevention of DoS (not UX)
- Dangerous operations (cleanup) are service methods, not endpoints (prevents accidental triggering)

### Implementation Metrics
- **Total Test Suite**: 187 tests passing, 86.73% coverage
- **Audit Tests**: 15 new (5 service, 5 routes, 5 integration)
- **New Code**: ~400 lines (models, service, router, schemas)
- **API Endpoints**: 3 (query logs, recent logs, suspicious activity)
- **Critical Fix**: Single-line JSON type change resolved 140+ test failures
- **Deployment Readiness**: Cross-database compatible, retention policy configured, admin endpoints ready

**Key Achievement**: Established comprehensive audit system supporting compliance, security monitoring, and operational investigation while maintaining single codebase for SQLite (test) and PostgreSQL (production).

## Docker Compose Dev Stack (Issue #20 - Story 7.1)

### Context
Implemented a full local development stack with PostgreSQL, Redis, MinIO, Meilisearch, and FastAPI in `docker-compose.yml`, plus onboarding and troubleshooting docs in `README.md`.

### Key Learnings

#### 1. **Keep Test and Dev Compose Files Separate**
- **Problem**: Reusing one compose file for both CI/testing and local development causes port and service-scope conflicts.
- **Solution**: Preserve `docker-compose.test.yml` for isolated test DB usage and add dedicated `docker-compose.yml` for full local stack.
- **Learning**: Separate compose files by lifecycle purpose (test vs dev) to avoid accidental coupling and flaky local setups.

#### 2. **Healthchecks Drive Reliable Startup Order**
- **Problem**: Service startup order with plain `depends_on` is not sufficient for readiness-sensitive apps.
- **Solution**: Add healthchecks to all infrastructure services and use `depends_on: condition: service_healthy` for the backend.
- **Learning**: For local multi-service stacks, readiness checks are essential to avoid startup race conditions and false failure reports.

#### 3. **Document Access Paths and Credentials in One Place**
- **Problem**: Developers lose time discovering service URLs, ports, and default credentials.
- **Solution**: Add a single quick-start section in `README.md` with service URLs, credentials, and standard lifecycle commands.
- **Learning**: A complete “first 5 minutes” runbook in README reduces onboarding friction more than scattered notes.

#### 4. **Troubleshooting Section Prevents Repeated Support Loops**
- **Problem**: Most local Docker issues are repetitive (port conflicts, stale volumes, missing rebuild, startup logs).
- **Solution**: Add targeted troubleshooting commands (`logs`, `down -v`, rebuild flow, conflict checks).
- **Learning**: Proactive troubleshooting guidance in docs significantly lowers recurring setup support overhead.

### Implementation Metrics
- **Files Added**: `Dockerfile`, `docker-compose.yml`
- **Files Updated**: `README.md`, `LEARNINGS.md`
- **Validation**: 188/188 tests passing, Black/isort checks passing

### Code Review Learnings (10 Copilot Review Comments)

#### 1. **Python Version Alignment Across Environments**
- **Problem**: Dockerfile used Python 3.13 but project tooling (GitHub Actions/CI, mypy, black) targeted 3.11.
- **Impact**: "Works in container but fails in CI" incompatibilities from dependency/typing differences.
- **Fix**: Changed Dockerfile base from `python:3.13-slim` to `python:3.11-slim`.
- **Learning**: Align ALL runtime environments (Docker, CI, local IDE) to single Python minor version declared in pyproject.toml.

#### 2. **Docker Editable Install Without Source**
- **Problem**: Builder stage ran `pip install -e .` after copying only `pyproject.toml`, causing build failures.
- **Root Cause**: Editable installs require source code at install time.
- **Fix**: Copy both `pyproject.toml` AND `app/` before install, use non-editable install (`pip install .`).
- **Learning**: For Docker multi-stage builds, install non-editable packages in builder stage.

#### 3. **Healthcheck Dependencies Not in Requirements**
- **Problem**: Dockerfile HEALTHCHECK used `import requests`, but `requests` not in dependencies → container stays unhealthy forever.
- **Fix**: Changed healthcheck to use stdlib `urllib.request` instead.
- **Learning**: Container healthchecks must use only stdlib or explicitly installed  dependencies.

#### 4. **Port Conflicts Between Dev and Test Compose**
- **Problem**: `docker-compose.yml` Redis port 6379 conflicted with `docker-compose.test.yml` Redis 6379, violating "no port conflicts" acceptance criteria.
- **Fix**: Changed dev Redis to port 6380, bound all service ports to `127.0.0.1` for security.
- **Learning**: Separate compose files must have disjoint port ranges; document port mapping decisions.

#### 5. **Security: Port Bindings Default to All Interfaces**
- **Problem**: Docker Compose port syntax `"8000:8000"` exposes on `0.0.0.0` (all interfaces), accessible from LAN despite docs claiming "localhost-only".
- **Fix**: Changed all port bindings to `"127.0.0.1:PORT:PORT"` to restrict to localhost.
- **Learning**: Always explicitly bind to `127.0.0.1` for local-only services to prevent accidental LAN exposure.

#### 6. **`:latest` Tags Break Reproducibility**
- **Problem**: MinIO/Meilisearch using `:latest` tag causes non-reproducible builds, surprise breaking changes on rebuild.
- **Fix**: Pinned to specific versions (MinIO `RELEASE.2025-02-26T08-46-43Z`, Meilisearch `v1.6.0`).
- **Learning**: Never use `:latest` in dev/prod compose files; pin to immutable tags with documented upgrade path.

#### 7. **Hardcoded Environment Variables vs `.env` File**
- **Problem**: App service hardcoded 30+ env vars in compose instead of loading from `.env`, causing config drift.
- **Story Requirement**: "Environment variables from .env injected" not met.
- **Fix**: Changed to `env_file: .env` with minimal compose-specific overrides (REDIS_HOST, REDIS_PORT).
- **Learning**: Use `env_file` for app config, only override infrastructure hostnames/ports in compose environment section.

#### 8. **Missing Acceptance Criteria: Bucket Auto-Creation**
- **Problem**: Story required MinIO bucket `nanos` auto-created on startup, but compose only started MinIO server.
- **Fix**: Added `minio_init` service with MinIO Client (mc) to create bucket after MinIO healthcheck.
- **Learning**: Infrastructure "init" services are essential for acceptance criteria requiring post-startup setup.

#### 9. **Documentation Accuracy: Service Descriptions**
- **Problem**: README claimed `docker-compose.test.yml` is "PostgreSQL-only" but actually includes Redis too.
- **Fix**: Updated description to "Minimal PostgreSQL + Redis environment for CI testing".
- **Learning**: Review existing files before documenting "what's already there" to avoid misleading descriptions.

#### 10. **Security Warnings in Documentation**
- **Problem**: README stated Redis is "localhost-only" without warning about no authentication, implying false security.
- **Fix**: Added explicit warnings: "no auth; development use only; do not expose to untrusted networks".
- **Learning**: Always document security implications of no-auth services, even if "localhost-only".

### Why These Issues Weren't Caught Initially
1. **Testing Gap**: No Docker build/run validation in the initial implementation.
2. **Version Mismatch**: Python 3.13 installed locally but project configured for 3.11 (not immediately obvious).
3. **Security Assumptions**: Port bindings to `0.0.0.0` are Docker default, requires explicit security awareness.
4. **Editable Install**: `pip install -e .` works locally with source present, masks Docker build context issue.
5. **Acceptance Criteria**: MinIO bucket creation wasn't in explicit checklist (story prose only).

### Review Process Value
- **10 substantial issues** caught by systematic PR review before merge.
- **Security improvements**: Localhost-only binding, explicit no-auth warnings.
- **Reproducibility**: Version pinning, Python version alignment.
- **Acceptance criteria completeness**: Bucket auto-creation now implemented.

**Time Investment**: Review fixes took ~30 minutes; would have cost hours of debugging in production.

## Compose Provisioning Hardening (Issue #27)

### Context
Implemented Sprint 2 infrastructure story `S2-OPS-01` to ensure PostgreSQL + MinIO can be provisioned reliably via `docker-compose`, with health checks, environment-driven credentials/endpoints, and restart-safe persistence behavior.

### Key Learnings

#### 1. **Environment-Driven Compose Config Prevents Drift**
- **Problem**: PostgreSQL and MinIO credentials/bucket values were hardcoded in `docker-compose.yml`.
- **Fix**: Switched to `${VAR:-default}` interpolation and added required variables in `.env.example`.
- **Learning**: Use env interpolation for infrastructure config even in local dev so credentials/endpoints are explicit, overridable, and documented.

#### 2. **Pinned Image Tags Can Become Invalid**
- **Problem**: The configured MinIO tag `RELEASE.2025-02-26T08-46-43Z` was no longer resolvable, causing compose startup failure.
- **Fix**: Replaced with a resolvable image reference (`minio/minio:latest`) to restore startup reliability.
- **Learning**: Validate referenced image tags in CI or preflight checks; an invalid tag silently blocks the entire local stack.

#### 3. **Init Containers Should Reuse Same Credential Source**
- **Problem**: MinIO bucket initialization used hardcoded credentials and bucket name.
- **Fix**: Passed `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, and `MINIO_BUCKET_NAME` into `minio_init` and reused them in `mc` commands.
- **Learning**: Bootstrap/init services must consume the same env contract as primary services to avoid hidden mismatch bugs.

#### 4. **Documentation Must Match Actual Port Mappings**
- **Problem**: README listed Redis on `localhost:6379` while compose mapped Redis to host `6380`.
- **Fix**: Corrected README and added explicit health/persistence verification commands.
- **Learning**: Always reconcile docs with effective container port mappings; stale docs create false-negative debugging paths.

#### 5. **Test Suite Reliability Depends on Explicit Service Prereqs**
- **Observation**: Full test runs can fail with Redis connection errors when required services are not running.
- **Learning**: Infrastructure-dependent test suites should have an explicit setup step (or pre-test task) that starts required containers deterministically.

## PR Review Follow-up Learnings (PR #36 - Issue #27)

### Context
After implementing Issue #27 (PostgreSQL + MinIO compose provisioning), Copilot AI reviewer identified 4 issues related to version pinning consistency, error handling, and documentation clarity. This review caught gaps that weren't identified during initial implementation or testing.

### Key Learnings

#### 1. **Version Pinning Must Be Consistent Across Stack**
- **Problem**: Fixed broken MinIO startup by switching from invalid tag to `:latest`, but this violated the version-pinning pattern used by all other services (Postgres 13-alpine, Redis 7-alpine, Meilisearch v1.6.0).
- **Root Cause**: Quick fix focused on "make it work" without checking existing patterns in the codebase.
- **Fix**: Changed from `minio/minio:latest` to pinned version `minio/minio:RELEASE.2023-12-23T07-19-11Z`.
- **Why it matters**: 
  - `:latest` is non-deterministic - future upstream releases can break local dev silently
  - Pinned versions ensure reproducible builds across team and time
  - Version updates become deliberate, documented decisions
- **Learning**: Before implementing infrastructure fixes, check existing service definitions for patterns (version pinning, naming, healthcheck style). Maintain consistency even under time pressure.
- **Process Gap**: Initial implementation didn't cross-reference other service definitions. Should have run `grep 'image:' docker-compose.yml` to identify pattern.

#### 2. **Init Containers Must Fail Fast, Not Silently Succeed**
- **Problem**: `minio_init` service ended with `exit 0;`, causing it to always succeed even if bucket creation failed.
- **Impact**: App service could start without initialized bucket because `depends_on: condition: service_completed_successfully` passed on failed init.
- **Root Cause**: Defensive programming gone wrong - `exit 0` added to prevent spurious failures but eliminated all failure signals.
- **Fix**: Removed `exit 0` and added `set -e` at start of script so shell exits on command failures.
- **Why it matters**:
  - Silent failures mask configuration problems until runtime
  - Dependencies on "successful" init are meaningless if init can't fail
  - Hard-to-debug issues (missing bucket) appear in application layer instead of infrastructure layer
- **Learning**: Init containers should fail fast and loudly. Use `set -e` for shell scripts. Never use unconditional `exit 0` - it defeats the entire purpose of exit codes.
- **Best Practice**: Test init container failures explicitly - simulate bad credentials, network issues, and verify container exits non-zero.

#### 3. **Documentation Labels Must Match Runtime Behavior**
- **Problem**: README labeled compose env vars as "Required" but `docker-compose.yml` provided defaults via `${VAR:-default}` pattern.
- **Impact**: Misleading for new contributors - they might think services won't start without .env file, when defaults actually work.
- **Root Cause**: Documentation written based on best practice ("you should set these") rather than actual behavior ("services work with defaults").
- **Fix**: Changed label from "Required" to "Optional: Override Docker Compose service defaults" and added explanation of when customization is needed.
- **Why it matters**:
  - False requirements create unnecessary onboarding friction
  - Contributors waste time creating .env files with duplicate defaults
  - Creates confusion when services work without "required" config
- **Learning**: Documentation must precisely reflect runtime behavior, not idealized practice. If variables have defaults, say "optional" and document the defaults. Reserve "required" for truly mandatory config.
- **Process Improvement**: When documenting config, test with and without .env file to verify true requirements.

#### 4. **Document Complete Configuration Chains, Not Just Components**
- **Problem**: README documented `POSTGRES_*` variables but didn't explain relationship to `DATABASE_URL` that FastAPI app actually uses.
- **Impact**: Users setting up compose Postgres don't realize they also need to configure `DATABASE_URL` for the app to connect.
- **Root Cause**: Infrastructure config and application config documented separately without explaining the connection.
- **Fix**: Added explicit documentation showing:
  - `POSTGRES_*` vars configure the container
  - `DATABASE_URL` is what app uses
  - Example: `DATABASE_URL=postgresql+asyncpg://diwei_user:diwei_password@localhost:5433/diwei_nano_market`
  - Shows how to build DATABASE_URL from POSTGRES_* values
- **Why it matters**:
  - Config with multiple layers (infra → app) must be documented end-to-end
  - Variable name differences (`POSTGRES_USER` vs `DATABASE_URL` username component) make relationship non-obvious
  - Without this, users hit "connection refused" errors and debug blindly
- **Learning**: For infrastructure provisioning, document the complete path from infrastructure config through to application usage. Show how variables flow between layers, especially when names differ.
- **Pattern**: When documenting env vars, always ask "what consumes this?" and "what else is needed for the feature to work?"

### Process Learnings

#### Why These Issues Weren't Caught Initially
1. **Testing Gap**: Initial testing focused on "does it start?" not "is it consistent with existing patterns?"
2. **Acceptance Criteria**: Story required health checks and persistence, but not explicit version pinning or init container failure testing
3. **Documentation Review**: README updates weren't tested with fresh perspective (simulating new contributor experience)
4. **Error Path Testing**: Init container happy path tested (bucket created), but failure scenarios not validated

#### Value of Systematic Code Review
- **4 substantial improvements** from review that passed tests and basic acceptance criteria
- **Categories**: Consistency (version pinning), reliability (error propagation), clarity (docs), completeness (config relationships)
- **Pattern**: All issues are about quality/maintainability, not functionality. All tests passed, but code wasn't production-ready.
- **Learning**: Passing tests + working features ≠ production-ready. Reviews catch consistency, patterns, edge cases, and future problems.

#### How to Prevent Similar Issues
1. **Pre-commit Checklist**: "Does this match patterns in existing code?"
2. **Error Path Testing**: Explicitly test failure scenarios for init/setup containers
3. **Documentation Testing**: Have someone unfamiliar with the code follow the docs
4. **Config Chain Mapping**: For infrastructure changes, document variable flow from infra → app
5. **Version Policy**: Establish and document policy on version pinning (never :latest)

### Implementation Metrics
- **Review Items**: 4 suggestions implemented (100% acceptance rate)
- **Files Modified**: 2 (docker-compose.yml, README.md)
- **Lines Changed**: ~15 lines (small surface area, high impact)
- **Test Impact**: No new tests needed (behavioral changes, not new features)
- **Time to Implement**: ~15 minutes after review (much faster than eventual debugging)

**Key Achievement**: Transformed working but fragile infrastructure config into production-ready pattern through systematic review. Emphasized importance of consistency, fail-fast behavior, and clear documentation even when functionality works.

---

## Database Migrations with Alembic & PostgreSQL Enums (Issue #22 - Nano Upload Domain Model)

### Context
Implemented database migrations for Sprint 2 Nano upload feature, establishing migration infrastructure and Nano domain models for upload workflow.

### Key Learnings

#### 1. **Alembic Setup with Async SQLAlchemy**
- Modified migrations/env.py for async patterns (async_engine_from_config, asyncio.run)
- Source database URL from environment at runtime
- Learning: Async ORM requires explicit async handling in Alembic

#### 2. **PostgreSQL Enum Types and Downgrade Safety**
- Auto-generated migrations create enums but don't clean them up on downgrade
- Solution: Add op.execute("DROP TYPE IF EXISTS myenum CASCADE") to downgrade()
- Learning: PostgreSQL enums persist after table drops and must be explicitly cleaned

#### 3. **Test Database Enum Cleanup**
- Pytest fixtures using Base.metadata.create_all() fail with existing enums
- Solution: Drop tables → drop orphaned enums → recreate everything
- Learning: Integration tests need explicit enum cleanup before create_all()

#### 4. **Nano Domain Model - Denormalization for Performance**
- Added cache fields (download_count, average_rating, rating_count) for UI metrics
- Learning: Denormalization acceptable when reads frequent and updates batched

#### 5. **Enum as Primary Semantic Entity**
- Use Python enums in code, let SQLAlchemy handle schema
- Learning: Never scatter state values across migrations and code

#### 6. **Foreign Key Strategy**
- Nano ownership: CASCADE delete (user deletion cascades to Nanos)
- Learning: CASCADE for ownership, SET NULL for audit trails

### Implementation Stats
- Files Modified: 5 | Migration: 1 (8 tables, 8 enums, 20+ indexes) | Tests: 188 passing
- Time: ~2 hours | Achievement: Production-ready migration infrastructure

## ZIP Upload API Endpoint (Issue #24 - Upload Implementation)

### Context
Implemented file upload endpoint with ZIP validation, authentication, and draft Nano creation. Required integrating JWT auth, file validation, database operations, and comprehensive testing for multipart form data handling.

### Key Learnings

#### 1. **UUID Type Consistency in Dependency Injection**
- **Problem**: Router defined `user_id: Annotated[str, Depends(get_current_user_id)]` while middleware returned `UUID`, causing SQLAlchemy error "'str' object has no attribute 'hex'"
- **Root Cause**: JWT middleware extracts UUID from token and returns it directly, but FastAPI parameter annotation declared string type
- **Solution**: Changed annotations to `user_id: Annotated[UUID, Depends(...)]` and added `from uuid import UUID` import
- **Why it matters**:
  - Type mismatches between dependency and annotation cause runtime errors
  - SQLAlchemy UUID columns require UUID objects, not strings
  - FastAPI respects type annotations for validation
- **Learning**: Match dependency injection parameter types exactly to what dependency function returns

#### 2. **File Validation Strategy - Defense in Depth**
- **Approach**: Implemented three-layer validation for ZIP files
  1. **Type validation**: Check MIME type AND file extension (not just one)
  2. **Size validation**: Stream file in chunks to enforce 100MB limit without loading entire file to memory
  3. **Structure validation**: Use `zipfile.ZipFile` to verify integrity and ensure non-empty content
- **Why layered validation**:
  - MIME type can be spoofed (need extension check)
  - Extension can be wrong (need MIME check)
  - Both can be correct but file corrupt (need structure check)
  - Size check must happen during streaming to prevent memory exhaustion
- **Learning**: File upload validation requires multiple complementary checks at different layers

#### 3. **Memory-Safe File Size Validation**
- **Problem**: Need to enforce 100MB upload limit without loading entire file into memory
- **Solution**: Stream file content in 1MB chunks, accumulate size, reject when threshold exceeded
  ```python
  while chunk := await file.read(1024 * 1024):
      total_size += len(chunk)
      if total_size > MAX_FILE_SIZE:
          raise HTTPException(status_code=413)
  ```
- **Why it works**:
  - Fixed chunk size prevents memory spikes
  - Early termination when limit exceeded (don't process entire oversized file)
  - Rewind file with `await file.seek(0)` after validation for downstream processing
- **Learning**: Stream-based validation protects against memory exhaustion attacks

#### 4. **String Truncation Logic Scope**
- **Problem**: Title truncation logic inside `if not title:` block meant explicit titles weren't truncated, causing test failure "expected 250==200"
- **Root Cause**: Truncation was only applied to auto-generated titles from filename
- **Solution**: Move `title = title[:200]` outside conditional so it applies to both explicit and generated titles
- **Why it matters**:
  - Database constraints require consistent length limits
  - Logic should apply uniformly regardless of title source
  - Tests revealed inconsistency when testing long explicit titles
- **Learning**: Apply data transformations (truncation, validation) consistently across all code paths that set a value

#### 5. **Testing Authenticated Endpoints**
- **Implementation**: Used `verified_user_id` fixture that:
  1. Creates test user in database
  2. Generates valid JWT token via `/auth/login` endpoint
  3. Returns tuple of (user_id, auth_headers) for test use
- **Pattern**: 
  ```python
  async def test_upload_requires_auth(async_client):
      response = await async_client.post("/api/v1/upload/nano", ...)
      assert response.status_code == 401  # No token
      
  async def test_upload_success(async_client, verified_user_id):
      user_id, headers = verified_user_id
      response = await async_client.post("/api/v1/upload/nano", headers=headers, ...)
      assert response.status_code == 201
  ```
- **Learning**: Test both authenticated and unauthenticated paths; use fixtures for auth setup to avoid repetition

#### 6. **ZIP Test Data Creation**
- **Approach**: Create in-memory ZIP files using `io.BytesIO` and `zipfile.ZipFile`
  ```python
  zip_buffer = io.BytesIO()
  with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
      zip_file.writestr("data.json", '{"test": "data"}')
  zip_buffer.seek(0)
  files = {"file": ("test.zip", zip_buffer, "application/zip")}
  ```
- **Why in-memory**:
  - No filesystem dependencies (faster, no cleanup)
  - Can create variations easily (empty ZIP, corrupt data, etc.)
  - Deterministic test behavior
- **Learning**: Use `io.BytesIO` for test file creation to avoid filesystem complexity

#### 7. **Validation Behavior Determines Test Expectations**
- **Discovery**: Initially wrote test `test_upload_nano_handles_filename_without_extension` expecting 201 success
- **Reality**: Validation correctly rejects files without `.zip` extension with 400 status
- **Resolution**: Renamed test to `test_upload_nano_rejects_filename_without_zip_extension` and changed assertion to `assert response.status_code == 400`
- **Why it matters**:
  - Tests should verify actual validation behavior, not assumptions
  - Implementation revealed stricter validation was correct design choice
  - Test names should reflect what actually happens
- **Learning**: When test fails, verify if implementation or test expectation is wrong; don't assume implementation is always incorrect

### Process Learnings

#### Module Organization for Upload Features
```
app/modules/upload/
  __init__.py           # Module marker
  schemas.py            # Pydantic request/response models
  validation.py         # File validation logic (type/size/structure)
  service.py            # Business logic (Nano creation)
  router.py             # FastAPI endpoint with auth integration
tests/modules/upload/
  test_validation.py    # Unit tests for validators (20 tests)
  test_service.py       # Unit tests for service layer (7 tests)
  test_upload_routes.py # Integration tests for API (11 tests)
```
- **Learning**: Separate concerns (validation, service, routing) into distinct files for maintainability

#### FastAPI File Upload Best Practices
1. Use `UploadFile` parameter type for automatic multipart parsing
2. Validate MIME type via `file.content_type`
3. Stream content with `await file.read(chunk_size)` for memory safety
4. Reset file position with `await file.seek(0)` after validation
5. Return appropriate HTTP status codes (400 validation, 413 too large, 201 created)

#### Testing File Uploads Checklist
- ✅ Valid upload (happy path)
- ✅ Authentication required (401 without token)
- ✅ Invalid file type (400 rejection)
- ✅ File too large (413 rejection)
- ✅ Empty ZIP (400 rejection)
- ✅ Corrupt ZIP (400 rejection)
- ✅ Database persistence verification
- ✅ Multiple uploads create separate records

### Implementation Stats
- **Files Created**: 10 (5 source, 5 test)
- **Files Modified**: 3 (main.py, conftest.py, IMPLEMENTATION_STATUS.md)
- **Tests Added**: 32 (validation: 20, service: 7, routes: 11)
- **Test Results**: 220/220 passing (188 existing + 32 new), 88.40% coverage
- **Code Quality**: Black ✅, isort ✅, no linting errors ✅
- **Time to Implement**: ~3 hours
- **Achievement**: Production-ready file upload endpoint with comprehensive validation and testing

### PR Review Follow-Up Learnings (Issue #24 / PR #38)

- **Review-only blind spot #1 (error exposure):** Generic exception handlers that return `str(e)` can leak internal details. Use stable client-facing messages and log full exceptions server-side.
- **Review-only blind spot #2 (test memory pressure):** Unit tests used very large in-memory payloads (50-101MB), which did not fail locally but can slow or destabilize CI.
- **Why this was caught in PR review and not initial implementation:** Local runs had sufficient memory headroom and no security-focused assertion for error detail leakage.
- **Prevention added:**
  - Reworked size tests to monkeypatch `MAX_UPLOAD_SIZE` and use small payloads while preserving boundary semantics.
  - Added test to assert unexpected ZIP parsing errors return a generic message and never expose internal exception text.
  - Updated ZIP structure validation to avoid reading full upload into memory via `await file.read()`.

### Docker Runtime Compatibility Learnings (Issue #39)

#### 1. Persisted Volume Format vs. Image Version
- **Problem**: Local Docker startup failed with persisted MinIO/Meilisearch volumes created by incompatible engine versions.
- **Symptoms**:
  - Meilisearch: database version mismatch (`1.36.0` vs engine `1.6.0`)
  - MinIO: `decodeXLHeaders: Unknown xl header version 3`
- **Learning**: Volume data formats are not downgrade-safe across all versions. Pinning service images without volume version strategy causes recurring local startup failures.

#### 2. Versioned Volume Names Reduce Hidden Drift
- **Approach**: Use explicit service-specific volume names tied to image/engine strategy (e.g., `meilisearch_data_v1_6_0`).
- **Learning**: Explicit volume naming makes data lifecycle and migration intent visible, avoiding accidental reuse of incompatible persisted state.

#### 3. Health Check Tooling Must Match Image Contents
- **Problem**: Health checks can fail when relying on tools not present in minimal images.
- **Learning**: Validate health command availability per image and prefer stable, image-compatible checks. A passing service process can still appear unhealthy if the health probe itself is invalid.

#### 4. Auxiliary Client Images Can Break on CLI Changes
- **Problem**: `minio/mc:latest` changed command behavior; `mc config host add` failed and required `mc alias set`.
- **Learning**: Initialization containers should use current CLI syntax and be reviewed when using floating tags.

#### 5. Compose Spec Evolution
- **Observation**: Compose warns that top-level `version` is obsolete and ignored.
- **Learning**: Remove obsolete keys to keep config future-compatible and reduce operator confusion during incident handling.

#### 6. Meilisearch Master Key in Development
- **Observation**: Meilisearch warns when no master key is set and auto-generates a key.
- **Learning**: Set `MEILI_MASTER_KEY` explicitly (env-driven) even in local Docker to align behavior with production security expectations and avoid runtime drift between environments.

## Docker Configuration & Environment Consistency (Issue #25 - Pre-Implementation Discovery)

### Context
During implementation of ZIP structure validation (Issue #25), discovered critical Docker configuration issues that prevented service startup. These pitfalls were not caught during normal development because the docker-compose environment was not validated as part of implementation workflow.

### Key Learnings

#### 1. **Image Tag Validity Must Be Verified Early**
- **Problem**: MinIO image tagged with specific release `minio/minio:RELEASE.2024-12-13T04-27-42Z` was not available (`docker.io/minio/minio:RELEASE.2024-12-13T04-27-42Z: not found`)
- **Root Cause**: Release tag had expired or wasn't published to Docker Hub; pinned version strategy didn't account for registry availability
- **Solution**: Changed to `minio/minio:latest` and documented reason in compose file
- **Learning**: When pinning image versions, always verify availability before committing. Use major version tags (e.g., `v1.6`) instead of specific release tags for better stability. Always test `docker compose pull` during implementation validation.

#### 2. **Persistent Volume Versioning Can Cause Incompatibility**
- **Problem**: Meilisearch volumes named `meilisearch_data_v1_6_0` contained database from older version (1.36.0) incompatible with current engine (1.6.0), causing restart loops with error: "Your database version (1.36.0) is incompatible with your current engine version (1.6.0)"
- **Root Cause**: Volume naming strategy included service version suffix, creating orphaned volumes when images were updated
- **Solution**: 
  - Renamed volume to generic `meilisearch_data` (no version suffix)
  - Removed old versioned volumes (`meilisearch_data_v1_6_0`, `minio_data_2024_12_13`, `minio_data_2024_12_18`, `minio_data_latest`)
  - Added cleanup step to compose validation workflow
- **Learning**: Never include service version numbers in volume names—this prevents data reuse when services are updated. Use generic names like `service_data` and manage compatibility through migration tooling instead.

#### 3. **Credential Alignment Across Related Services**
- **Problem**: MinIO server defined credentials as `MINIO_ROOT_USER: minioadmin`, `MINIO_ROOT_PASSWORD: minioadmin`, but MinIO init container used `MINIO_ROOT_PASSWORD: minioadmin123` (different password)
- **Result**: Init container tried to authenticate to MinIO server and failed: "The request signature we calculated does not match the signature you provided"
- **Root Cause**: Services were configured independently without validation of cross-service consistency
- **Solution**: 
  - Made MinIO server credentials env-driven: `MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}`
  - Ensured both services used identical environment variables from same source
  - Added validation rule: "All related services sharing credentials must use identical defaults"
- **Learning**: When multiple related services use shared credentials (databases, auth servers, object storage), validate they use **identical values** at compose-up time. Create a pre-flight checklist that verifies credential alignment before considering environment valid.

#### 4. **Environment Variable Consistency in Test vs. Runtime**
- **Problem**: Application configured Redis on port 6379 by default, but docker-compose mapped Redis to port 6380 (mismatch: `"127.0.0.1:6380:6379"`)
- **Result**: Tests failed with `ConnectionRefusedError` on port 6380 because app tried to connect to 6379
- **Root Cause**: Port mappings were not documented in config files or .env, causing developers to guess correct values
- **Solution**:
  - Fixed mapping to `"127.0.0.1:6379:6379"` (standard Redis port)
  - Added .env documentation showing REDIS_HOST/REDIS_PORT/REDIS_URL values
  - Modified `app/redis_client.py` to call `get_settings()` dynamically instead of caching at import time
  - Added `pytest_configure` hook to load .env early in test lifecycle
- **Learning**: Document all environment-specific port mappings in `.env.example`. Validate by running tests without manual env var setup—if tests require `export REDIS_URL=...`, the configuration is wrong. Configuration should work automatically from .env.

#### 5. **Environment Validation Should Precede Implementation**
- **Problem**: These Docker/config issues only surfaced when the implementation was nearly complete and ready for testing
- **Root Cause**: No early validation step existed in workflow to catch environment issues
- **Solution**: Added "Environment Validation" section to `nano_implement.prompt.md` to be performed before implementation begins
- **Learning**: Treat development environment integrity as a **blocking prerequisite**, not a secondary concern. Issues with Docker, credentials, or config should be discovered and fixed before implementation work starts, not discovered mid-implementation.

#### 6. **Docker Compose Environment Variables vs Host Machine Localhost**
- **Problem**: Setting `REDIS_URL=redis://localhost:6379/0` in `.env` file worked for local tests but broke Docker Compose app container
- **Root Cause**: When Docker Compose loads `.env` via `env_file: .env`, the app container interprets `localhost` as the container's own localhost (container network isolation), not the `redis` service accessible via Docker network service name
- **Manifestation**: Container would fail to connect to Redis with connection refused error, even though Redis service was healthy
- **Solution**:
  - Documented in `.env.example` that REDIS_URL should differ between local development (`redis://localhost:6379/0`) and Docker Compose (`redis://redis:6379/0`)
  - Recommended leaving REDIS_URL unset in `.env` and using REDIS_HOST/REDIS_PORT/REDIS_DB fallback instead
  - Added explicit `REDIS_URL` override in `docker-compose.yml` app service environment to use service name: `REDIS_URL: "redis://redis:6379/0"`
  - This ensures Docker Compose always uses correct service name regardless of `.env` contents
- **Why This Wasn't Caught Earlier**: Tests ran on host machine where `localhost` correctly resolved to Redis. Docker Compose app container networking wasn't validated during initial implementation.
- **Learning**: When using `env_file` in Docker Compose, environment variables containing hostnames (`localhost`, IP addresses) may have different meanings inside vs. outside containers. Always override network-sensitive environment variables (database URLs, service endpoints) explicitly in the compose service `environment` section to use Docker service names (`redis`, `postgres`, `minio`). Document environment-specific values clearly in `.env.example` and consider leaving URL-formatted variables unset by default to force explicit configuration per environment.

---

## Sprint 2 - MinIO Storage Integration (Issue #23)

### Implementation Date
2026-03-03

### Key Learnings

#### 1. **Mock Fixture Design: Callable vs Static Return Values**
- **Problem**: Test failed with `TypeError: 'str' object is not subscriptable` when mock returned static string but test passed UUID object as parameter
- **Context**: `test_upload_with_storage_integration` attempted `mock_storage.upload_file(nano_id=verified_user_id)` where `verified_user_id` is a UUID object. Mock was configured with `mock_instance.upload_file.return_value = "mocked-storage-key"` (static string)
- **Root Cause**: When mock's return_value is a static value, the mock still accepts arguments but ignores them. However, test code expected `upload_file()` to be callable with `nano_id` parameter, not to subscript the UUID
- **Solution**: Changed mock from static return value to callable function:
  ```python
  def mock_upload_file(content: bytes, filename: str, nano_id: UUID):
      return f"nanos/{nano_id}/content/{filename}"
  
  mock_instance.upload_file = mock_upload_file
  ```
- **Learning**: When mocking methods that accept parameters used in the mock's logic, use callable functions instead of static return values. This ensures parameter types are validated and mock behavior matches actual implementation signatures. Static return_value is appropriate only when parameters don't affect the outcome.

#### 2. **Object Storage Adapter Pattern for External Dependencies**
- **Problem**: Need to integrate MinIO object storage without creating tight coupling between business logic and storage implementation
- **Solution**: Created `MinIOStorageAdapter` as separate module with well-defined interface:
  - `upload_file()`: Accepts bytes and returns storage key
  - `delete_file()`: Removes object by key
  - `get_file_url()`: Generates presigned download URLs
  - `object_exists()`: Checks existence without download
- **Benefits**:
  - Service layer (`create_draft_nano()`) receives storage adapter via dependency injection
  - Tests can inject mock adapter without MinIO dependency
  - Storage implementation can be swapped (e.g., S3, Azure Blob) without changing service logic
  - HTTP error handling (503) isolated to router layer
- **Learning**: For external dependencies like object storage, databases, or third-party APIs, use the adapter pattern with dependency injection. This enables isolated testing, flexible error handling, and decoupled architecture. Define clear interface boundaries between business logic and infrastructure concerns.

#### 3. **Deterministic Object Key Naming for Idempotency**
- **Problem**: Need consistent storage paths for uploaded files to support retries and avoid orphaned objects
- **Solution**: Implemented deterministic key generation using Nano UUID:
  ```python
  def _generate_object_key(self, nano_id: UUID, filename: str) -> str:
      return f"nanos/{nano_id}/content/{filename}"
  ```
- **Benefits**:
  - Repeated uploads with same nano_id overwrite previous file (idempotent)
  - Storage path directly reflects database relationship (Nano UUID → storage key)
  - Simplifies cleanup: delete Nano record → delete `nanos/{uuid}/` prefix
  - Enables bulk operations on Nano-specific objects
- **Alternative Considered**: Random/timestamped keys would require database tracking of all storage keys and complex cleanup logic
- **Learning**: For object storage keys, prefer deterministic naming based on domain identifiers (UUIDs, entity IDs) over random keys. This enables idempotent operations, simplifies data lifecycle management, and maintains clear relationships between storage and database records. Use hierarchical path structure (`nanos/{uuid}/content/{filename}`) to support efficient prefix-based operations.

#### 4. **Graceful Degradation with HTTP 503 for Storage Failures**
- **Problem**: MinIO unavailability should not return generic 500 errors or expose internal details
- **Solution**: 
  - Custom `StorageError` exception propagates from storage layer to router
  - Router catches `StorageError` and returns HTTP 503 with user-friendly message
  - 503 status indicates temporary unavailability, signaling clients to retry later
- **Error Handling Strategy**:
  - Retry logic (3 attempts) in storage adapter for transient failures
  - If retries exhausted, raise `StorageError` with original exception details
  - Router translates `StorageError` to HTTP 503: "Object storage temporarily unavailable"
  - Other exceptions (validation, database) remain separate with appropriate status codes
- **Learning**: For external service dependencies (storage, payment gateways, email services), implement three-tier error handling: (1) Retry transient failures at the adapter layer, (2) Raise custom exception when retries exhausted, (3) Translate to appropriate HTTP status code at API layer. Use HTTP 503 (Service Unavailable) for temporary infrastructure issues to signal retry-able failures vs HTTP 500 (Internal Server Error) for unrecoverable bugs. This provides graceful degradation and actionable feedback to API consumers.

#### 5. **MinIO Configuration Management via Environment Variables**
- **Problem**: MinIO requires multiple configuration values (endpoint, credentials, bucket, secure/insecure, region)
- **Solution**: Added 10 MinIO-related settings to `app/config.py`:
  - Connection: `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`
  - Bucket: `MINIO_BUCKET_NAME`, `MINIO_REGION`
  - Behavior: `MINIO_SECURE` (TLS), `UPLOAD_MAX_RETRIES`, `UPLOAD_TIMEOUT_SECONDS`
  - Presigned URLs: `MINIO_PRESIGNED_URL_EXPIRY_SECONDS`
- **Benefits**:
  - Local development: `MINIO_SECURE=false` with `localhost:9000`
  - Production: `MINIO_SECURE=true` with TLS endpoint
  - Tuning: Adjust retry/timeout behavior per environment
- **Learning**: For services with multiple configuration dimensions (connection, credentials, behavior tuning), create granular environment variables instead of composite connection strings. This provides finer control across environments and simplifies debugging (e.g., toggle TLS separately from endpoint). Document sensible defaults in code and provide `.env.example` with environment-specific values.



## Async Timeout Enforcement & Retry Semantics (Issue #26 - Upload Retry + Timeout Handling)

### Context
Implemented upload timeout guardrails (10 minutes), retry semantics for transient failures, and explicit failure-state visibility in the upload API.

### Key Learnings

#### 1. Async Context Manager Timeouts with asyncio.wait_for()
- Use asyncio.wait_for(operation, timeout=seconds) for hard timeout boundaries
- Wrap synchronous blocking operations with asyncio.to_thread() to keep event loop free
- Preserves async/await syntax while enforcing timeout deadlines

#### 2. Transient Error Classification via Pattern Matching
- Pattern-match on exception message string for transient indicators: timeout, connection, 503, 429, dns
- Distinguish recoverable failures (retry) from terminal failures (fail fast)
- Avoids library-specific exception catching while working across exception hierarchies

#### 3. Exponential Backoff with Bounded Maximum
- Formula: min(2.0, 0.25 * (2**attempt)) bounds backoff to 2 seconds max
- Prevents unbounded growth from exceeding timeout window
- With 3 retries: total delay <= 6 seconds (well within 600-second timeout)

#### 4. Structured Error Responses with Explicit Retry Policy
- Add explicit fields to error response: failure_state, retryable, retry_after_seconds
- Include HTTP header Retry-After: 30 (RFC 7231 standard)
- Enables client retry policies and distinguishes rate-limited from permission errors

#### 5. Thread Pool Blocking I/O with Async
- Use asyncio.to_thread() to execute sync operations in thread pool
- Compose with asyncio.wait_for() for timeout enforcement
- Keep event loop free during blocking I/O operations

#### 6. Timeout Configuration in HTTP Clients
- Configure urllib3.Timeout with separate values: connect (10s), read (600s), total (600s)
- Use min(10, total) for connect timeout to stay within total budget
- Provides fine-grained control vs global timeout integers

### Implementation Stats (Issue #26)
- Files Modified: 8 (config, storage, service, router, schemas, tests, doc)
- Pattern: Async timeout + transient classification + exponential backoff + structured errors
- Test Results: 240/240 passing, 89% coverage
- Timeout Enforcement: 600 seconds (10 minutes)
- Max Retry Backoff: 2 seconds
- Max Retry Attempts: 3
- Docker Validation: All services healthy


## Comprehensive Upload & Storage Testing (Issue #28 - S2-BE-06)

### Context
Implemented complete test suite for upload endpoint, ZIP validation, DB persistence, and MinIO integration covering all acceptance criteria while maintaining CI safety with optional real MinIO testing.

### Key Learnings

#### 1. **Multi-Layer Test Organization for Complex Workflows**
- Organized tests into logical layers: validation (21 tests), service layer (9 tests), storage (19 tests), API endpoints (10 tests), real MinIO optional (1 gated test)
- Each layer has clear responsibility, enabling targeted test runs and maintainability
- Clear documentation of system architecture through test organization

#### 2. **CI-Safe Default with Optional Real Integration Testing**
- Pattern: Default mock-based tests (CI-safe) with @pytest.mark.skipif(os.getenv("RUN_REAL_MINIO_TESTS") != "1") for optional real tests
- Execution: pytest tests/ (240 passed, 1 skipped) vs RUN_REAL_MINIO_TESTS=1 pytest ... (enables real MinIO)
- Documented in README with clear activation instructions

#### 3. **Mock Adapter Pattern for External Services**
- Use conftest.py fixture to patch adapter at module import level
- Preserve service contracts (return types, exceptions)
- Deterministic behavior enables fast, network-independent testing

#### 4. **Acceptance Criteria to Test Mapping**
- Criterion 1 (upload handlers): 10 endpoint tests
- Criterion 2 (ZIP edge cases): 8 structure tests
- Criterion 3 (DB persistence): Explicit file_storage_path verification
- Criterion 4 (MinIO CI-safe + optional): 19 mocked + 1 real (gated) test
- Systematic mapping ensures complete coverage

#### 5. **Environment Integrity Validation**
- Process: docker pull → compose up → health check → config audit → compose down
- Validations: credential consistency, port uniqueness, image tag resolvability, health checks
- All checks passed for current setup

### Implementation Stats (Issue #28)
- Files Modified: 3 (test_storage.py, README.md, LEARNINGS.md)
- Tests: 240 passed, 1 skipped, 89.08% coverage
- Acceptance Criteria: 4/4 met
- Quality: Black/isort compliant
- Docker: All services healthy

### PR Review Follow-up (Issue #28)
- Optional real-integration tests should use best-effort cleanup in `finally` blocks so cleanup failures do not mask the primary assertion failure.
- Manual implementation stats in documentation can drift after late edits; include a final pre-push consistency check against `git diff --name-only` to keep file counts accurate.

## Frontend Bootstrap Baseline (Issue #32 - S2-FE-01)

### Context
Implemented the first frontend workspace for the project using React 18 + Vite + strict TypeScript and aligned repository documentation for Windows/PowerShell-first development.

### Key Learnings
- Keep frontend bootstrap minimal for the first issue: app shell + strict TS + feature-folder skeleton is enough to unblock parallel FE stories.
- Validate `npm run dev` with a short smoke run and accept automatic port fallback (`5173` to `5174`) to avoid false failures when local ports are busy.
- Use `npm run build` (`tsc -b && vite build`) as the strongest bootstrap health check because it validates both TS project references and bundling.
- Maintain separation of concerns from day one: `src/app`, `src/features`, `src/shared` improves scalability for Story 8.x follow-up issues.
- Backend validation tasks can remain unchanged while frontend is added, but frontend-specific checks should be run explicitly in `frontend/`.

## Copilot PR Review Follow-Up (PR #45 - S2-FE-01)

### Context
Implemented 8 Copilot AI review suggestions for the frontend bootstrap PR, focusing on configuration cleanup, security hardening, and TypeScript build artifact management.

### Key Learnings
- **TypeScript build artifacts (`*.tsbuildinfo`) should never be committed**: These are machine/version-specific incremental build cache files. Add to `.gitignore` and configure `tsBuildInfoFile` to write to `node_modules/.cache/` to keep the repo clean.
- **`process.env` in vite.config.ts requires `@types/node`**: When using Node.js globals like `process.env` for configuration (e.g., conditional dev server host), install `@types/node` as a devDependency to satisfy TypeScript in project references (`tsconfig.node.json`).
- **Vite dev server `host: true` exposes to all network interfaces (0.0.0.0)**: This is a security risk by default. Use `host: process.env.VITE_DEV_SERVER_HOST ?? "localhost"` to bind to localhost unless explicitly configured for LAN access.
- **Project references require `tsc -b` for proper typechecking**: When `tsconfig.json` uses `references` instead of `include`, the `typecheck` script must use `tsc -b --noEmit` (not `tsc --noEmit`) to check all referenced projects.
- **Duplicate config files create confusion**: Having both `vite.config.ts` and `vite.config.js` leads to unpredictable behavior. Delete the generated `.js` file when using TypeScript config as the source of truth.
- **TypeScript composite projects can emit artifacts unexpectedly**: When `composite: true` is set without `noEmit: true`, `tsc -b` will generate `.d.ts` declaration files and `.tsbuildinfo` even if the intent is typecheck-only. Always add `noEmit: true` for non-library projects.
- **Copilot AI review comments should be treated like human reviews**: They provide actionable inline suggestions with rationale. Implement systematically using the `mcp_github_pull_request_read` tool's `get_review_comments` method to discover all threads.
- **Frontend-only changes don't require backend Docker infrastructure for validation**: When changes are isolated to frontend config (tsconfig, vite.config, package.json), validate with `npm run typecheck` and `npm run build` instead of waiting for Redis/PostgreSQL to start.

---

## Tailwind CSS v3 Setup & Design Token Management (Issue #31 - S2-FE-02)

### Context
Implemented Tailwind CSS + design tokens for DiWeiWei frontend. Encountered version compatibility issues and learned differences between Tailwind CSS v3 and v4 PostCSS plugins.

### Key Learnings

#### 1. **Tailwind CSS v3 vs v4 PostCSS Plugin Differences**
- **Problem Initially**: Installed `@tailwindcss/postcss` (v4 beta plugin) which requires different CSS syntax (`@import "tailwindcss"` instead of `@tailwind` directives)
- **Solution**: Use **Tailwind CSS v3** for stable production: `npm install -D tailwindcss@3`
- **Why it matters**: v3 uses traditional @tailwind directives; v4 beta has breaking changes; v3 is production-tested; mismatches cause "Cannot apply unknown utility class" errors
- **Learning**: Use v3 for production Tailwind until v4 reaches stable release. Check npm registry version tags before installing.

#### 2. **PostCSS Config File Extensions for ES Modules**
- **Problem**: Created `postcss.config.js` with TypeScript types, but got "Unexpected token" error because `package.json` has `"type": "module"`
- **Solution**: Rename to `postcss.config.cjs` (CommonJS) when project uses ES modules
- **Why it matters**: Node.js treats .js as ES modules; PostCSS needs CommonJS; mismatch causes immediate SyntaxError
- **Learning**: Use .cjs extension for CommonJS tools in ES module projects. Runtime compatibility>TypeScript type safety.

#### 3. **Design Token Scope: Config vs Runtime Constants**
- **Problem**: Created extensive custom tokens in config that weren't available as CSS utilities
- **Solution**: Separate concerns: Config for utilities (colors, fontSize); tokens.ts for programmatic access
- **Why it matters**: Tailwind only generates utilities from config theme; JS code needs imported constants; over-config inflates bundle
- **Learning**: Tailwind config generates CSS; for JS/TS token access, always maintain separate tokens.ts mirror.

#### 4. **Base Styles Best Practice**
- **Problem**: Adding many element defaults in `@layer base` felt repetitive
- **Solution**: Use base sparingly for resets/defaults, @layer components for classes, inline utilities for unique styling
- **Why it matters**: Base has high priority; utility-first means override at component level; debuggability
- **Learning**: Reserve @layer base for global defaults. Use @layer components for reusable classes.

#### 5. **Color Palette Incremental Testing**
- **Problem**: Created 66 colors (6 groups × 11 shades); build failed with "unknown utility class"
- **Solution**: Start minimal (neutral, primary, secondary); add semantic colors gradually with testing
- **Why it matters**: Comprehensive systems need stability; catches issues early; team feedback loop
- **Learning**: Design systems benefit from incremental addition with validation. Don't deploy entire system at once.

#### 6. **Component Utilities via @layer components**
- **Achievement**: Created reusable classes (.btn-primary, .card-elevated, .container-main) using @layer components
- **Pattern**: Low specificity allows utilities to override; self-documenting; reduces JSX repetition
- **Learning**: @layer components bridges utility-first and DRY code. Use for frequently repeated combinations.

#### 7. **Build Performance: CSS Size & Gzipping**
- **Result**: Generated CSS 8.49 kB (2.23 kB gzipped) for 66 colors + utilities
- **Why it matters**: Reasonable size; 73% compression validates CSS is repetitive utility rules; unused utilities tree-shaken
- **Learning**: Comprehensive Tailwind doesn't bloat production if configured correctly. Gzip metrics validate approach.

### Implementation Stats
- Files Created: 3 | Files Modified: 4
- Build Time: ~3 sec | CSS: 8.49 kB → 2.23 kB (gzip)
- Design Tokens: 66 colors + 8 font sizes + utilities
- Component Classes: 6 primary utilities

#### 8. **Why PR Review Found Issues Not Caught Initially**
- **Gap**: Initial validation focused on build success (`npm run typecheck`, `npm run build`) and did not include a checklist for config-level safety and documentation correctness.
- **What review caught**: Missing explicit `font-sans` on `body`, inaccurate usage example import path, broad terminal auto-approve commands, and incomplete Tailwind base color keys.
- **Prevention**: Add a lightweight pre-PR checklist for (1) docs/examples runnable correctness, (2) security-sensitive workspace config changes, and (3) theme/config compatibility keys that can impact downstream utilities.
- **Learning**: Build-green is necessary but not sufficient; include a small review-ready checklist for non-runtime quality gates.

---

## Sprint 2 Frontend: Centralized HTTP Client Configuration (Issue #34 - S2-FE-04)

### Context
Implemented centralized Axios HTTP client with environment-based configuration and JWT token injection for Sprint 2 frontend work. Prepared infrastructure for token refresh implementation in Sprint 3.

### Key Learnings

#### 1. **Environment-First API Configuration in Vite Projects**
- Use `import.meta.env.VITE_*` for public API variables (accessible in browser)
- Provide sensible defaults: `VITE_API_BASE_URL ?? "http://localhost:8000"`
- Test configuration availability during development mode with validation function
- **Why it matters**:
  - Public vs private environment variables prevent secret leakage
  - Defaults enable development without `.env.local` file
  - Validation catches misconfiguration early (development mode warning)
- **Learning**: Vite's `import.meta.env` system requires explicit VITE_ prefix by design. Document this pattern prominently to prevent developers from trying to access private environment variables from client code.

#### 2. **Token Storage Pattern: localStorage with Structured Object**
- Store tokens as JSON object in localStorage: `{ accessToken, refreshToken, expiresIn }`
- Use consistent key name: `auth_tokens` to enable easy lookup across app
- Gracefully handle JSON parsing errors (corrupted localStorage) without breaking requests
- **Pattern**:
  ```typescript
  const storedTokens = localStorage.getItem("auth_tokens")
  if (storedTokens) {
    try {
      const tokens = JSON.parse(storedTokens)
      if (tokens.accessToken) {
        // Inject bearer token
      }
    } catch (error) {
      // Silently ignore corrupted data
    }
  }
  ```
- **Learning**: Assume localStorage can be corrupted or manipulated. Defensive parsing prevents crashes but doesn't validate token integrity (that's the server's job during verification).

#### 3. **Request Interceptor: Transparent Token Injection**
- Inject `Authorization: Bearer {token}` header automatically for every request
- No manual header management needed in component code
- Interceptor runs before request sent (no async operation delay)
- **Benefits**:
  - Single point of token injection (DRY principle)
  - Consistent behavior across entire application
  - Components stay focused on business logic, not auth infrastructure
- **Pattern**: Interceptor should be silent (no logging in production) and return original config unchanged if no token exists (allows public endpoints)

#### 4. **Response Interceptor: Error Handling Preparation**
- Handle 401 (Unauthorized) specially: clear tokens and dispatch event for app-level redirect
- Pass other errors through for app-specific handling
- Design with clear placeholder for Sprint 3 token refresh logic
- **Current Sprint 2 Behavior**:
  - On 401: Remove tokens, dispatch `auth:unauthorized` custom event
  - App listens for event and redirects to login page
  - No automatic retry (that's Sprint 3)
- **Sprint 3 Preparation**:
  - Comments document token refresh flow
  - Placeholder shows exactly where refresh logic goes
  - Structure supports async token refresh with original request retry
- **Learning**: Plan for future enhancements (token refresh) in initial interceptor design. Use comments to document where logic will go so future implementers understand architectural assumptions. This prevents inconsistent error handling patterns later.

#### 5. **Development Logging: Conditional Console Output**
- Use `if (import.meta.env.DEV)` for development-only logging
- Log request method/URL and response status
- Enable debugging without production log spam
- **Pattern**:
  ```typescript
  if (import.meta.env.DEV) {
    console.debug(`[API] ${method} ${url}`, data)
  }
  ```
- **Learning**: Production code should not include debug logs. Use environment checks to keep logging only in development. Format logs consistently with clear prefixes `[API]` to enable searching in console.

#### 6. **Error Messages: User-Friendly vs Technical**
- 401 errors get explicit message: "Unauthorized request - 401"
- Error details logged in development mode only
- No leakage of exception messages to end users
- **Why it matters**:
  - User-friendly errors reduce support burden
  - Technical details (backend stack traces) never leak to client
  - Log levels determine what operators see vs what users see
- **Learning**: Distinguish between user-facing error messages and technical logs. Users see "Unauthorized, please login". Operators see "401 Unauthorized: user_id not found in token claims". Never expose technical details to users.

#### 7. **Axios Singleton Pattern for Consistent Configuration**
- Create single `httpClient` instance configured at module load
- Export singleton for use throughout application
- Configuration applied once, reducing overhead and ensuring consistency
- **Pattern**:
  ```typescript
  const httpClient = axios.create({
    baseURL: API_CONFIG.BASE_URL,
    timeout: API_CONFIG.REQUEST_TIMEOUT,
  })
  setupInterceptors(httpClient)
  export const httpClient // Re-exported from all modules
  ```
- **Learning**: HTTP client is infrastructure singleton similar to database connections. Create once at startup, reuse everywhere. Dependency injection at the HTTP client level (importing from `shared/api`) is simpler than passing through function parameters.

#### 8. **Testing HTTP Client Without Running Server**
- Client configuration tests verify environment loading and default values
- Interceptor tests mock request/response to verify logic without network
- Integration tests use real server (in E2E phase)
- **Test Pattern**:
  - Token injection: Mock axios interceptor, verify Authorization header added
  - 401 handling: Mock error response, verify tokens cleared
  - Missing token: Verify request proceeds without Authorization header
- **Learning**: Unit tests for HTTP client can verify configuration and interceptor logic without network. Full end-to-end tests require real backend.

#### 9. **Documentation: Examples vs Auto-Generated Docs**
- Auto-generated docs (Swagger/OpenAPI) document backend API contract
- HTTP client library requires separate documentation with usage examples
- Include both "quick start" (most common use case) and detailed reference
- **Pattern**:
  ```typescript
  // Quick start
  const user = await httpClient.get("/api/v1/auth/me")
  
  // With error handling
  try {
    await httpClient.post("/api/v1/auth/login", { email, password })
  } catch (error) {
    if (error.response?.status === 401) {
      // Handle unauthorized
    }
  }
  ```
- **Learning**: Library documentation should teach usage patterns, not just document functions. Include examples for common patterns (authenticated requests, error handling, token storage).

#### 10. **Configuration Validation as Documentation**
- Configuration validation exists in code comments showing expected variables
- Warnings in development catch missing/invalid configuration
- Validation doesn't block startup (sensible defaults exist)
- **Function**: `validateApiConfig()` checks for common mistakes:
  - Missing VITE_API_BASE_URL → suggests http://localhost:8000
  - Very low REQUEST_TIMEOUT → suggests it's probably misconfigured
- **Learning**: Validation is more useful as development assistant than as hard errors. Warn users about suspicious values but allow sensible defaults to work. Help developers self-diagnose instead of requiring documentation lookups.

#### 11. **Sprint Structure: Small Infrastructure Features**
- S2-FE-04 (this issue): HTTP client configuration (1 PT)
- S2-FE-05 (next): React Query client setup
- S2-FE-06 (future): Token refresh implementation
- Architecture built in layers: (1) Transport (HTTP client), (2) State management (React Query), (3) Auth flow (token refresh)
- **Learning**: Multi-sprint frontend work benefits from layered architecture. Start with transport layer (HTTP client), add caching layer (React Query), then add auth orchestration (token refresh). This enables testing each layer independently and swapping implementations later.

#### 12. **Why Configuration Issues Didn't Block Implementation**
- Vite development server has sensible defaults (http://localhost:5173 for frontend, assumes http://localhost:8000 for backend API)
- No production build/deployment was required for this feature
- Tests passed without running actual API server (unit tests only)
- **What would catch issues**: Running frontend against real backend + running tests in mounted Docker volume
- **Prevention**: Next sprint should include baseline E2E test that starts both frontend + backend and validates communication

### Implementation Metrics
- **Files Created**: 7 (config, httpClient, interceptors, index, examples, README, test)
- **Configuration**: Vite environment variables + .env.example
- **Dependencies Added**: axios@^1.7.0
- **Documentation**: Comprehensive README with token flow diagrams
- **Test Coverage**: Unit tests for configuration, interceptors, error handling
- **Acceptance Criteria**: All 3 met (base URL from env, token injection, error handling prepared)

### Key Achievement
Established frontend infrastructure for Sprint 2+ frontend work. Provided solid foundation for React Query (S2-FE-05) and token refresh (S2-FE-06) in future sprints. Documented token flow clearly to enable Sprint 3 implementation without rework.
## Router Skeleton & Validation Reliability (Issue #30 - S2-FE-03)

### Context
Implemented the React Router v6 baseline with placeholder MVP routes and fallback handling, while validating the mixed frontend/backend task workflow on Windows PowerShell.

### Key Learnings

#### 1. **Group future-protected routes early to avoid route churn**
- **Approach**: Added a dedicated `ProtectedRouteLayout` with `Outlet` and nested `/dashboard`, `/profile`, `/admin` under it.
- **Why it matters**: Sprint 3 auth checks can be added in one place without rewriting the route map or changing public paths.
- **Learning**: Introduce route hierarchy scaffolding before auth logic to reduce refactor risk.

#### 2. **Keep fallback behavior explicit in the first router iteration**
- **Approach**: Added a wildcard `*` route with a dedicated placeholder page.
- **Why it matters**: Unknown URLs are handled deterministically and acceptance criteria are testable.
- **Learning**: Include explicit fallback routes from day one; do not rely on implicit default behavior.

#### 3. **Frontend-only feature work still needs minimal runtime checks**
- **Observation**: `npm run typecheck` + `npm run build` validated TypeScript and bundling quickly, but project policy still required `Checks` and verified backend-aware test execution.
- **Learning**: Use layered validation: fast frontend checks first, then repository-wide checks required by workflow.

#### 4. **Health-check credentials in automation must match compose defaults**
- **Problem observed**: `Test: Verified` can fail if PostgreSQL probe credentials drift from `docker-compose.yml` defaults.
- **Why it matters**: Infrastructure may be healthy while task falsely reports failure.
- **Learning**: Keep task-level health probes aligned with compose/env defaults to avoid false negatives in CI/dev workflows.

#### 5. **404 fallback copy should include a concrete action**
- **Problem observed**: A not-found page message suggested returning to known routes but provided no direct navigation path.
- **Fix**: Added explicit CTA link (`Back to Home`) to `/` in the fallback page.
- **Learning**: When UX text instructs user action, include a matching interactive element to avoid dead-end screens and review feedback.

## React Query Provider Composition & Frontend Tooling (Issue #35 - S2-FE-05)

### Context
Implemented React Query client/provider composition in the frontend root and added a sample query path for smoke validation, while stabilizing TypeScript/Vitest integration in a mixed frontend/backend repository.

### Key Learnings

#### 1. **Vitest config typing requires `vitest/config` when using `test` in Vite config**
- **Problem**: TypeScript reported `test` as unknown when `defineConfig` was imported from `vite`.
- **Fix**: Import `defineConfig` from `vitest/config` in `frontend/vite.config.ts`.
- **Learning**: For co-located Vite + Vitest config, use the Vitest-typed config entrypoint to avoid TS overload errors.

#### 2. **Provider ownership should be centralized to prevent router duplication**
- **Problem**: `BrowserRouter` existed in router module and was added again at provider layer.
- **Fix**: Move router ownership to `AppProviders` and keep `AppRouter` focused on route definitions only.
- **Learning**: Centralized provider composition prevents duplicated context providers and keeps app bootstrap logic predictable.

#### 3. **Axios interceptor handler internals need defensive typing in tests**
- **Problem**: Direct assertions on `interceptors.*.handlers` caused strict TypeScript errors (`possibly undefined`, `InternalAxiosRequestConfig` mismatch).
- **Fix**: Use optional chaining/non-null assertions where appropriate and cast mock configs carefully in tests.
- **Learning**: Interceptor internals are implementation-detail-heavy; tests should balance strict typing with targeted assertions.

#### 4. **On Windows PowerShell, avoid Unix utilities (`head`, `tail`) in scripted checks**
- **Problem**: `head`/`tail` commands failed in PowerShell during verification steps.
- **Fix**: Run direct commands or use PowerShell-native alternatives when output filtering is needed.
- **Learning**: Cross-shell command assumptions can hide validation output and slow down debugging.

#### 5. **README drift is easy after frontend feature additions unless root docs are updated immediately**
- **Problem**: Root README did not reflect newly completed frontend story scope and tooling.
- **Fix**: Updated top-level status, frontend feature summary, and test/build commands to match implementation state.
- **Learning**: Treat root README as release-facing documentation and update it in the same implementation cycle as feature code.


## Frontend Quality Tooling & Docker Compose Integration (Issue #33 - S2-FE-06)

### Context
Issue #33 required setting up ESLint/Prettier for code quality, a dev proxy for API requests, and a Docker Compose service for frontend static asset serving. This completed the frontend infrastructure bootstrap for Sprint 2.

### Implementation Summary

#### 1. **ESLint + Prettier Setup**
- **Challenge**: Peer dependency conflicts between ESLint 9+ and eslint-plugin-react-hooks (expects ESLint 8)
- **Solution**: Pinned eslint@^8.57.0, typescript-eslint@^7.18.0, and eslint-plugin-react@^7.36.1 for compatibility
- **Configuration**:
  - `.eslintrc.json` - React, TypeScript, and hooks rules enabled
  - `.prettierrc.json` - LF line endings, 100-char print width, standard formatting
  - `.eslintignore` / `.prettierignore` - Exclude dist, node_modules, config files
- **Scripts**:
  - `npm run lint` - Check code quality
  - `npm run lint:fix` - Auto-fix ESLint violations
  - `npm run format` - Apply Prettier formatting
- **Learning**: Frontend tooling version compatibility requires careful pin management. Test `npm install` early to catch peer dependency conflicts before pushing code.

#### 2. **Vite Dev Proxy Configuration**
- **Purpose**: Forward `/api/*` requests from frontend to backend during development
- **Implementation**: Added proxy config to `vite.config.ts`:
  ```typescript
  proxy: {
    "/api": {
      target: process.env.VITE_API_BASE_URL ?? "http://localhost:8000",
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ""),
    },
  }
  ```
- **Behavior**: 
  - Dev server on `:5173` proxies `/api/auth/login` to `http://localhost:8000/auth/login`
  - Respects `VITE_API_BASE_URL` environment variable for flexibility
  - Strips `/api` prefix before forwarding to backend
- **Learning**: HTTP client must be configured to use `/api` prefix URLs for proxy to intercept. Backend and frontend can develop independently on different ports during dev.

#### 3. **Frontend Docker Compose Service**
- **Challenge**: Frontend state is stateless (built HTML/CSS/JS) but needs backend at :8000 available
- **Solution**: 
  - Created `Dockerfile.frontend` with multi-stage build (Node.js builder → Nginx server)
  - Builder stage: Runs TypeScript check + Vite production build
  - Server stage: Nginx Alpine serves `/dist` artifacts on port 80
  - Health check: Curl `/health` endpoint every 10 seconds
- **Docker Compose**:
  - Added `frontend` service on `:3000` (mapped from container port 80)
  - Depends on `app` service health check (waits for backend readiness)
  - Uses named `Dockerfile.frontend` to avoid conflicts with backend Dockerfile
- **Nginx Configuration**:
  - SPA routing: `try_files $uri $uri/ /index.html` for React Router
  - Cache-busting: Static assets (js/css) cached with 1-year immutable headers
  - Gzip compression enabled by Nginx defaults
- **Learning**: Frontend Docker service should enforce backend readiness via health checks. SPA serving requires special Nginx config to route all unknown paths to index.html.

#### 4. **Frontend Test Execution & Linting**
- **Issue Found**: Unused `waitFor` import in useUserProfile.test.ts was flagged by ESLint
- **Fix**: Removed unused import to satisfy linting checks
- **Test Results**: 11 tests passing (9 HTTP client + 2 React Query hook tests)
- **Build Output**: Production bundle with gzipped JS (~62.5KB), CSS (~2.17KB)
- **Learning**: Frontend tests must be executable without backend (uses mocked httpClient). Linting should pass before commits to prevent CI failures.

#### 5. **Documentation Parity**
- **Updated**: 
  - `frontend/README.md` - Added comprehensive dev proxy, Docker, and script documentation
  - Documented API proxy behavior and multi-terminal workflow
  - Included Docker Compose deployment section with multi-stage build explanation
- **Learning**: Quality tooling docs should cover not just what's available but when/why each script is needed (e.g., dev proxy only works with `/api` prefixed URLs).

### Acceptance Criteria Status

✅ **Lint + formatting scripts available and passing**
- ESLint and Prettier configured and all checks pass
- `npm run lint`, `npm run lint:fix`, `npm run format` scripts available

✅ **Dev proxy forwards API requests to backend**
- Vite proxy configured to forward `/api/*` to backend :8000
- VITE_API_BASE_URL env var allows customization

✅ **Compose service exists for frontend static artifact serving**
- Dockerfile.frontend with multi-stage build and Nginx SPA routing
- Frontend service on :3000 with health checks and dependency on backend

✅ **npm run build produces deployable bundle**
- Production build outputs to `dist/` with TypeScript checking
- Gzipped bundle ready for Nginx static serving

### Dependencies Resolved

✅ S2-FE-01 (React 18 + Vite + TypeScript baseline)
✅ S2-FE-02 (Tailwind CSS styling)
✅ S2-FE-03 (HTTP client & React Query) - S2-FE-04 and S2-FE-05
✅ S2-FE-06 (Quality tooling) - This issue

### Known Issues & Future Improvements

1. **TypeScript Version Compatibility**: typescript-eslint warns about TypeScript 5.9.3 vs. supported <=5.6.0. Not blocking but worth monitoring for major updates.
2. **ESLint v8 Usage**: Using v8 instead of latest v9 due to ecosystem compatibility. Plan to upgrade when plugins catch up.
3. **Frontend Tests Not in Main Suite**: Frontend tests run separately (`npm test`). Backend test suite (`pytest`) doesn't include frontend. Consider unified test execution in Sprint 3.
4. **No Pre-commit Hooks**: Linting/formatting not enforced before git commits. Consider husky + lint-staged for CI/CD pipeline.
5. **Token Storage Security**: Current implementation stores access and refresh tokens in `localStorage`, exposing them to XSS attacks. Sprint 3 should migrate refresh tokens to `HttpOnly`, `Secure` cookies and keep access tokens in short-lived memory only.

### Technical Debt

- Audit npm vulnerabilities (2 moderate severity found). Consider `npm audit fix` after verifying no breaking changes.
- Deprecation warnings for eslint@8 - plan ESLint 9 upgrade when react-hooks plugin stabilizes.


## Frontend Quality Tooling PR Review (Issue #33 - PR #50 Review Implementation)

### Context
After implementing ESLint/Prettier and Docker Compose integration (Issue #33, PR #50), Copilot AI reviewer identified 5 critical issues with Vite proxy configuration, environment variable loading, and security patterns.

### Key Learnings

#### 1. **Vite Proxy Path Rewriting Must Match Backend Routes**
- **Problem**: Proxy config had `rewrite: (path) => path.replace(/^\/api/, "")` which strips `/api` prefix
- **Impact**: Frontend calls to `/api/v1/auth/me` would be forwarded as `/v1/auth/me` but backend routes expect `/api/v1/*`, causing 404s
- **Root Cause**: Assumed backend was mounted at root instead of verifying actual route prefixes
- **Fix**: Removed rewrite rule - backend routes already include `/api/v1/*` prefix
- **Learning**: Always verify actual backend route structure before configuring proxies. Use `grep` to find router prefix definitions.

#### 2. **Vite Config Doesn't Auto-Load Environment Variables**
- **Problem**: Used `process.env.VITE_API_BASE_URL` directly in `vite.config.ts` but Vite doesn't load `.env` files into `process.env` for config file context
- **Impact**: Environment variables from `.env.local` would be ignored, always using hardcoded defaults
- **Fix**: Changed to function-based config with `loadEnv(mode, process.cwd(), '')` to explicitly load environment variables
- **Why it wasn't caught**: Dev testing used defaults (localhost:8000) which happened to match, so bug was silent
- **Learning**: Vite config files need explicit `loadEnv()` - unlike application code where Vite auto-injects `import.meta.env.VITE_*`. Test with non-default env values to catch config loading issues.

#### 3. **Prettierignore Pattern Specificity**
- **Problem**: Used generic `*.lockfile` pattern which doesn't match actual lock file names (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`)
- **Impact**: Lock files would still be formatted if Prettier ran outside `src/` directory
- **Fix**: List actual lock file names explicitly instead of using catching pattern
- **Learning**: Glob patterns in ignore files should match actual file naming conventions. Don't assume generic patterns will work - verify against real filenames.

#### 4. **localStorage Token Security Is Known Sprint 3 Gap**
- **Finding**: Storing tokens in `localStorage` exposes them to XSS attacks enabling token theft and account takeover
- **Status**: Documented as known technical debt for Sprint 3 token security implementation
- **Plan**: Migrate to `HttpOnly`, `Secure` cookies for refresh tokens and short-lived memory-only access tokens
- **Learning**: Security reviewers will flag Web Storage for sensitive data even if it's planned for later. Document known gaps explicitly in "Known Issues" sections to avoid repeated review cycles.

### Implementation Impact Analysis

**Why These Were Caught in PR Review:**
1. **Proxy rewrite bug**: No integration test exercising actual frontend → backend API calls through proxy
2. **Env loading bug**: Development always used default values matching actual setup, masking the loading failure
3. **Prettierignore**: Lock files are normally gitignored so Prettier never ran on them to expose the pattern issue

**Testing Improvements Needed:**
- Add integration test that exercises Vite dev proxy with non-default backend URL
- Add test that verifies `.env.local` variables are honored in Vite config
- Verify ignore patterns match actual files in repository

### Process Improvements

1. **Proxy configuration verification**: Always grep backend codebase for route prefixes before configuring proxies
2. **Environment variable testing**: Test all env-based config with non-default values to ensure loading works
3. **Ignore pattern validation**: Check ignore patterns against actual files in repository, not assumed naming conventions
4. **Security gap documentation**: Proactively document known security limitations in PR descriptions to set reviewer expectations
