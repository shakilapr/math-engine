# MathEngine Implementation Plan

**Date**: 2026-02-10  
**Version**: 1.0  
**Project**: MathEngine (math-engine)  
**Base Directory**: e:/projects/math-engine

## 1. Overview

This document provides a step‑by‑step plan for achieving the user's directive: "write test cases and test every little thing. use /test folder for testing. test every function, every math given. breakdown problems, and rename as needed. run and test. improve. until everything work well, tune and edit, and improve. fix all broken functionalities. make architecture.md and update it while doing each changes. specially, break 2022.md into multiple text, and feed one at a time to see how it works. check each and every script as well. also check frontend issues. test, qa, develop, and fix."

The plan is organized into phases, each with specific tasks, expected outputs, and success criteria.

## 2. Phase 1: Foundation & Setup

### Goals
- Establish a clean test directory structure.
- Create utilities for splitting 2022.md.
- Run existing tests to establish baseline.

### Tasks
1. **Create test directory structure** as outlined in `testing_strategy.md`:
   - `test/unit/`, `test/integration/`, `test/e2e/`, `test/test‑cases/`.
2. **Write splitting script** `scripts/split_2022.py`:
   - Input: `test/sample-text-problems/2022.md`
   - Output: individual JSON files in `test/test‑cases/2022/`
   - Each JSON includes problem statement, category, expected answer (if known), tolerance.
3. **Run existing test suite** (`pytest test_engine.py test_comprehensive.py test_detailed.py`) and record failures in `test‑results/baseline_failures.md`.
4. **Identify broken functionalities** from test failures and feature‑analysis.md.
   - Categorize: LLM code generation issues, execution errors, verification mismatches, frontend bugs.

### Deliverables
- Structured test directories.
- Split 2022 problems (20+ JSON files).
- Baseline failure report.

## 3. Phase 2: Unit Testing & Coverage

### Goals
- Achieve 100% function coverage for core modules (excluding scripts that self‑edit).
- Fix any unit‑level bugs discovered.

### Tasks
1. **Write missing unit tests** for each core module:
   - `backend/core/engine.py` – test `MathEngine.solve` with mocked LLM and executor.
   - `backend/core/executor.py` – test safe execution, timeout, error handling.
   - `backend/core/verifier.py` – test cross‑library verification.
   - `backend/core/explainer.py` – test step explanation generation.
   - `backend/core/visualizer.py` – test plot generation (mock matplotlib).
   - `backend/core/self_edit.py` – test file editing operations.
   - `backend/core/self_improve.py` – test improvement loop.
2. **Run coverage** (`pytest --cov=backend/core --cov-report=html`) and ensure all public functions are covered.
3. **Fix unit‑level bugs**:
   - Adjust mock behavior where needed.
   - Ensure edge cases (empty input, malformed LaTeX) are handled gracefully.

### Deliverables
- Complete unit test suite.
- Coverage report showing >95% line coverage for core modules.
- Fixed unit‑level bugs.

## 4. Phase 3: Integration Testing

### Goals
- Validate interactions between components.
- Ensure the full pipeline works for a variety of problem types.

### Tasks
1. **Write integration tests**:
   - `test/integration/test_pipeline.py`: Feed split 2022 problems through the full engine (with real LLM calls, but optionally mocked for speed).
   - `test/integration/test_library_integration.py`: Test script library matching and skill application.
   - `test/integration/test_image_pipeline.py`: Test image‑to‑LaTeX‑to‑solution flow using sample images.
   - `test/integration/test_pdf_pipeline.py`: Test PDF extraction and solving.
2. **Run integration tests** and record failures.
3. **Analyze failures**:
   - If LLM code generation is wrong, adjust prompts or add skill templates.
   - If execution fails, improve `SafeExecutor` or library imports.
   - If verification mismatches, investigate tolerance or library‑specific differences.
4. **Iterate** until all integration tests pass.

### Deliverables
- Integration test suite.
- Passing integration tests for text, image, PDF inputs.
- Documentation of any required prompt/library adjustments.

## 5. Phase 4: Frontend Testing & QA

### Goals
- Identify and fix frontend issues.
- Ensure UI works end‑to‑end with backend.

### Tasks
1. **Review frontend issues** from feature‑analysis.md:
   - Visualization images not displaying.
   - Editable equations not implemented.
   - Chat not fully integrated.
   - No markdown rendering in chat.
2. **Create frontend test suite**:
   - Component tests with React Testing Library for `Solver.tsx`, `ChatSidebar.tsx`, `MathRenderer`.
   - UI interaction tests (simulate input, click solve, verify results display).
   - Visual regression tests (optional).
3. **Run end‑to‑end tests** using Playwright:
   - Simulate user submitting a problem, verify steps appear.
   - Test image upload.
   - Test PDF analysis page.
4. **Fix identified issues**:
   - Ensure visualization images are served and displayed.
   - Implement equation editing (add “edit” button, LaTeX editor, recomputation).
   - Integrate chat context with solving.
   - Add markdown support in chat.

### Deliverables
- Frontend component tests.
- E2E test suite.
- Fixed frontend issues.

## 6. Phase 5: Self‑Editing & Improvement Loop

### Goals
- Ensure self‑editing capabilities work correctly.
- Use self‑improvement to fix broken scripts.

### Tasks
1. **Test self‑edit component**:
   - Simulate a failure (e.g., linear‑programming problem).
   - Trigger `SelfImprover` to analyze failure and propose edit.
   - Verify edit is applied correctly.
   - Re‑test to confirm fix.
2. **Automate the loop**:
   - Create a script that runs the split 2022 problems, detects failures, and triggers self‑improvement.
   - Record which problems were fixed automatically.
3. **Validate script library**:
   - Ensure each script in `backend/scripts/library/` is functional.
   - Add missing scripts for uncovered problem types.

### Deliverables
- Self‑edit test suite.
- Automated improvement loop.
- Verified script library.

## 7. Phase 6: Performance & Stress Testing

### Goals
- Identify performance bottlenecks.
- Ensure system handles concurrent requests.

### Tasks
1. **Benchmark critical paths**:
   - Time `MathEngine.solve` for various problem complexities.
   - Measure LLM call latency.
2. **Stress test** with multiple concurrent requests (using `locust` or custom script).
3. **Optimize** where needed:
   - Cache LLM responses for similar problems.
   - Parallelize verification across libraries.
   - Optimize image/PDF processing.

### Deliverables
- Performance benchmark report.
- Stress test results.
- Optimization recommendations.

## 8. Phase 7: Documentation & Finalization

### Goals
- Update architecture.md with changes.
- Ensure all documentation is current.

### Tasks
1. **Update architecture.md**:
   - Reflect any architectural changes made during testing/fixing.
   - Add diagrams for new components.
2. **Update feature‑analysis.md** with new completion percentages.
3. **Create user guide** for using the system.
4. **Generate final test report** summarizing coverage, passing tests, remaining issues.

### Deliverables
- Updated architecture.md.
- Updated feature‑analysis.md.
- Final test report.

## 9. Success Criteria

1. **Test Coverage**: 100% function coverage for core modules.
2. **Test Passing**: All unit, integration, and E2E tests pass.
3. **Problem Solving**: All split 2022 problems produce a correct or plausible answer.
4. **Frontend Functionality**: No console errors; all UI features work as expected.
5. **Self‑Improvement**: System can automatically fix at least one broken script.
6. **Documentation**: architecture.md and testing_strategy.md are up‑to‑date.

## 10. Timeline & Iteration

This plan is iterative: each phase may reveal issues that require revisiting earlier phases. The process should follow:

1. **Plan** → **Execute** → **Test** → **Analyze** → **Fix** → **Repeat**.

2. **Daily checkpoints**:
   - Run full test suite.
   - Update todo list.
   - Update architecture.md if significant changes.

3. **Completion**: When all success criteria are met.

## 11. Next Immediate Steps

1. Create the test directory structure.
2. Write splitting script for 2022.md.
3. Run existing tests and catalog failures.
4. Begin writing missing unit tests for `executor.py`.

---

*This plan will be updated as work progresses.*