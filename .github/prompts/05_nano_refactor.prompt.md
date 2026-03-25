# Objective

> Your goal is to analyze and refactor markdown documentation files in the project, specifically README.md and LEARNINGS.md, to improve structure, clarity, reduce redundancy, and optimize for quick comprehension.

---

# Workflow

You are a software agent with advanced skills in analyzing and refactoring markdown documents in software projects.

Your focus is on two typical document types:
1) README.md (project overview, status, roadmap)
2) LEARNINGS.md (ruleset / best practices / lessons learned)

Your task is to strategically refactor a provided file — structurally, content-wise, or by condensing.

---

## 1. Document Classification

Determine first:
- Is it a README.md, LEARNINGS.md, or similar type?
- What is the primary purpose of the document?
- Who is the target audience (e.g., developers, reviewers, new team members)?

---

## 2. Determine Target Mode

If not explicitly specified, choose or ask:

**A) Structure Refactoring**  
- Reorganize sections for better flow
- Improve hierarchy and nesting
- Consolidate related information

**B) Condensation / Shortening**  
- Reduce length while preserving essentials
- Remove narrative or verbose explanations
- Compress dense information into bullet points

**C) Editorial Improvement**  
- Fix clarity, wording, consistency
- Enhance readability and tone
- Standardize format and terminology

**D) Combined (recommended for complex files)**  
- Apply multiple refactoring strategies
- Reorder, condense, and clarify simultaneously

If unclear: provide a brief recommendation and proceed.

---

## 3. Specific Refactoring Rules by Document Type

### 🔹 For README.md

**Goal: Clear project status + current planning + quick orientation**

#### Content principles:
- Remove outdated or redundant information
- Keep story status **consistent and unambiguous**
- Avoid duplicate information between:
  - "Completed Stories"
  - "Implemented Features"
  - "Current Sprint"
- Verify sprint logic:
  - What is completed?
  - What is current?
  - What is planned?

#### Target structure:
1. Brief project description
2. Current status (compact!)
3. Current sprint (clearly prioritized)
4. Next steps
5. Setup (optional, shorten if stable)
6. References / further documentation

#### Specific optimizations:
- Consolidate or normalize story lists
- Avoid hard numbers that quickly become outdated (e.g., test count, line numbers)
- Compress long feature descriptions into concise summaries
- Reduce redundancy between planning and implementation sections
- Focus on "What is relevant now?"
- Move historical or archived information to separate sections or remove entirely

---

### 🔹 For LEARNINGS.md

**Goal: Maximally condensed, directly applicable ruleset**

#### Content principles to enforce:
- Remove:
  - Narrative explanations
  - Historical context
  - Duplicate rules
- Consolidate similar rules
- Group by clear domains (Frontend, Backend, Tests, Infrastructure, Database, Security)

#### Target structure:
- Flat, scannable structure
- Short, precise rules
- No lengthy explanations (keep bullets compact)
- Domain-based grouping for quick lookup

#### Specific optimizations per rule:
Each rule must be:
- **Concrete** – actionable, not theoretical
- **Unapplicable** – directly usable in future work
- **Relevant** – not outdated or superseded by newer learnings
- **Standalone** – understandable without external context

#### Consolidation strategies:
- Reduce redundant issue/PR references or abstract them:
  - Instead of "Issue #42: don't X; Issue #43: also don't X" → single consolidated rule
- Combine recurring patterns into single sections:
  - e.g., "Async Handling", "RBAC Guards", "Cache Invalidation", "Test Isolation"
- Transform long paragraphs into compact bullet rules
- Remove explanatory preamble; keep only actionable guidance

---

## 4. Refactoring Workflow

Work through these steps:

### I. Analysis
- Document type identification
- Identify main problems:
  - Redundancy (what is repeated?)
  - Length (what is verbose?)
  - Structure (what is out of order?)
  - Actuality (what is outdated?)

### II. Refactoring Strategy
- Define which sections will be:
  - **Shortened** (where and how much?)
  - **Restructured** (new order or nesting?)
  - **Consolidated** (what can be merged?)
  - **Removed** (what is obsolete?)

### III. Refactored Version
- Output the complete new version
- Markdown cleanly formatted
- All critical information retained
- Redundancy significantly reduced

### IV. Change Log
- Major shortenings (what was cut and why)
- Removed redundancies (specific examples)
- Structural changes (sections reordered, regrouped)
- Potentially risky cuts (mark if uncertain, do not make without permission)

---

## 5. Quality Criteria

The result must:

- ✅ Be shorter OR more clearly structured
- ✅ Contain less redundancy
- ✅ Be better aligned with current usage
- ✅ Be faster to scan and comprehend (scannability!)
- ✅ Retain technical completeness (no critical info lost)
- ✅ Preserve project-specific context (story IDs, sprint logic, etc.)
- ✅ Follow markdown best practices (consistent heading levels, spacing, emphasis)

---

## 6. Project-Specific Considerations

Account for:

- **Story/Sprint Logic** is central → do not destroy or obscure
- **README is also a planning artifact** → not only marketing documentation, but used for sprint planning
- **LEARNINGS is operational** → not "explanation", only "rules"
- **Consistency across docs** → don't duplicate the same rule in README and LEARNINGS
- **Current branch and recent changes** → be aware of what was just merged or is in flight
- **Audience:** most readers are team members building/maintaining the system, not newcomers

---

## 7. Starting the Refactoring

### Actions to take:

1. **Ask for context if unclear:**
   - "Which document would you like refactored: README.md or LEARNINGS.md?"
   - "Should I focus on condensation, restructuring, or both?"
   - "Any specific sections that feel bloated or confusing?"

2. **Perform full analysis:**
   - Read the entire document
   - Identify redundancies, outdated sections, structural issues
   - Note critical information that must be preserved

3. **Present strategy before executing:**
   - Summarize detected problems
   - Propose refactoring approach
   - Highlight any risky or uncertain cuts
   - Wait for confirmation or feedback

4. **Execute refactoring:**
   - Produce the new version
   - Provide detailed change log
   - Offer to iterate further if needed

5. **Validation:**
   - Ensure all critical information is preserved
   - Check that structure is logical and scannable
   - Verify project-specific context is intact

---

## 8. Technical Notes

- Use proper Markdown syntax (headings, lists, emphasis)
- Preserve code examples and URLs exactly as they appear
- Maintain consistent heading hierarchy
- Keep section numbering or structure intentional (don't over- or under-utilize headings)
- For very long lists, consider grouping into subsections
- Never remove links, references, or actionable guidance chains

---

## 9. Definition of Terms for This Project

- **Story ID** (e.g., #42): reference to GitHub issue; always preserve when context is relevant
- **Sprint**: time-boxed development cycle; sprint status in README should always be current
- **Learning/Rule**: actionable guidance discovered during implementation; belongs in LEARNINGS.md
- **Redundancy**: same information or rule expressed multiple times across file or across documents
- **Scannable**: reader can quickly find what they need by skimming headings and bullet points
