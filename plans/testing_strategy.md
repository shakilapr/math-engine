# MathEngine Comprehensive Testing Strategy

**Date**: 2026-02-10  
**Version**: 1.0  
**Project**: MathEngine (math-engine)  
**Base Directory**: e:/projects/math-engine

## 1. Overview

This document outlines a systematic testing strategy for the MathEngine project, ensuring every component is thoroughly validated, broken functionalities are fixed, and the system achieves robust reliability. The strategy aligns with the user's directive: "write test cases and test every little thing. use /test folder for testing. test every function, every math given. breakdown problems, and rename as needed. run and test. improve. until everything work well, tune and edit, and improve. fix all broken functionalities."

## 2. Scope

Testing will cover all core modules, API endpoints, frontend components, and integration points.

### 2.1 Backend Core Modules
- `backend/core/engine.py` – Main orchestrator
- `backend/core/executor.py` – Safe code execution
- `backend/core/verifier.py` – Cross‑library verification
- `backend/core/explainer.py` – Step‑by‑step explanations
- `backend/core/visualizer.py` – Math visualization
- `backend/core/self_edit.py` – Self‑editing capabilities
- `backend/core/self_improve.py` – Self‑improvement loop

### 2.2 Input Processing
- `backend/input/parser.py` – LaTeX, text, image parsing
- `backend/pdf/analyzer.py` – PDF extraction
- `backend/scripts/library_manager.py` – Script library management

### 2.3 LLM and Skills
- `backend/llm/provider.py` – Multi‑provider LLM integration
- `backend/skills/registry.py` – Skill matching and execution

### 2.4 API Layer
- `backend/api/routes/` – REST endpoints
- `backend/api/models.py` – Data models

### 2.5 Frontend (React/TypeScript)
- `frontend/src/pages/Solver.tsx` – Main solving interface
- `frontend/src/pages/Papers.tsx` – Research paper editing
- `frontend/src/pages/SelfEvolution.tsx` – Self‑evolution dashboard
- `frontend/src/components/` – Reusable UI components
- `frontend/src/lib/` – Utilities

### 2.6 Test Data
- `test/sample-text-problems/2022.md` – Break into individual problems
- `test/sample-image-problems/` – Image‑based test cases
- `test/sample-research-papers/` – PDF test documents

## 3. Testing Approach

### 3.1 Unit Testing
- **Goal**: Test each function in isolation.
- **Framework**: pytest (already configured)
- **Coverage Target**: 100% line coverage for core modules (excluding scripts that self‑edit).
- **Strategy**:
  - Write test cases for every public method.
  - Mock external dependencies (LLM calls, file I/O).
  - Validate edge cases and error handling.

### 3.2 Integration Testing
- **Goal**: Test interactions between components.
- **Examples**:
  - `engine.solve()` with mocked LLM and executor.
  - Input parser → LLM → executor → explainer pipeline.
  - Library manager loading and matching scripts.

### 3.3 End‑to‑End (E2E) Testing
- **Goal**: Validate the full user workflow.
- **Scenarios**:
  - Submit a text problem via UI, receive solution, steps, verification.
  - Upload an image, get LaTeX extraction, solution.
  - Load a PDF, extract equations, solve.
  - Use self‑editing to modify a script and verify it works.

### 3.4 Regression Testing
- **Goal**: Ensure fixes do not break existing functionality.
- **Method**:
  - Maintain a growing suite of test problems (from 2022.md and others).
  - Run before each commit.

### 3.5 Performance & Stress Testing
- **Goal**: Identify bottlenecks.
- **Metrics**: Execution time, memory usage, concurrent request handling.
- **Tools**: pytest‑benchmark, custom timing decorators.

## 4. Test Organization

### 4.1 Directory Structure
```
test/
├── unit/                    # Unit tests
│   ├── core/
│   │   ├── test_engine.py
│   │   ├── test_executor.py
│   │   └── ...
│   ├── input/
│   ├── llm/
│   └── skills/
├── integration/             # Integration tests
│   ├── test_pipeline.py
│   └── test_library_integration.py
├── e2e/                     # End‑to‑end tests
│   ├── test_ui_workflow.py
│   └── test_full_solve.py
├── sample‑problems/         # Test data (already exists)
│   ├── text/
│   ├── image/
│   └── pdf/
├── test‑cases/              # Curated test case definitions
│   ├── calculus.json
│   ├── linear_algebra.json
│   └── ...
└── test‑results/            # Generated test reports
```

### 4.2 Naming Conventions
- Unit test files: `test_<module>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<scenario>[_<variant>]`
- Integration test files: `test_<component>_integration.py`
- E2E test files: `test_e2e_<workflow>.py`

### 4.3 Test Data Management
- Each test problem should be stored as a separate file (JSON or YAML) containing:
  - Problem statement (LaTeX/text)
  - Expected category
  - Expected answer (if deterministic)
  - Allowed tolerance
- Break `2022.md` into individual problem files (see Section 7).

## 5. Coverage Goals

- **Function Coverage**: 100% of all public functions in core modules.
- **Branch Coverage**: >90% for critical decision points.
- **Math Coverage**: Every mathematical domain supported (calculus, linear algebra, complex analysis, etc.) must have at least one passing test.
- **Input Format Coverage**: Text, LaTeX, image, PDF.

**Tooling**: Use `pytest‑cov` to generate coverage reports.

## 6. Process: Test‑Improve‑Iterate

1. **Write Test Cases**
   - For each module, create unit tests covering all functions.
   - For each problem in `2022.md`, create an integration test.

2. **Run Test Suite**
   - Execute `pytest test/unit/` and `pytest test/integration/`.
   - Record failures in `test‑results/failures.md`.

3. **Analyze Failures**
   - Categorize failures: bug in code, insufficient LLM prompting, environment issue, etc.
   - Prioritize fixing broken functionalities.

4. **Fix and Improve**
   - Edit code, adjust prompts, update library scripts.
   - Use self‑editing capabilities where appropriate.

5. **Re‑run Tests**
   - Verify fixes pass.
   - Ensure no regression.

6. **Update Documentation**
   - Update `architecture.md` with changes.
   - Update `feature‑analysis.md` with new completion percentages.

7. **Repeat** until all tests pass and system meets quality criteria.

## 7. Breaking Down 2022.md

The file `test/sample-text-problems/2022.md` contains 20+ mixed‑format problems. It will be split into individual test cases.

### 7.1 Splitting Strategy
- Each **Question** (including sub‑parts) becomes a separate file.
- Use blank lines and "Question" markers as delimiters.
- Output format: JSON with fields:
  ```json
  {
    "id": "2022_q1",
    "problem": "Find the area between the parabolas $y^{2}=x$ and $x^{2}=y.$",
    "category": "calculus",
    "source": "2022.md",
    "expected_answer": "1/3",
    "tolerance": 1e-6
  }
  ```

### 7.2 Automation Script
Create a Python script `scripts/split_2022.py` that:
- Reads `2022.md`
- Splits by "Question" or "Q" patterns.
- Writes each problem to `test/test‑cases/2022/` as `.json`.

### 7.3 Feeding One at a Time
- A test runner (`test_runner.py`) will iterate over each split problem, feed it to `MathEngine.solve()`, and record results.
- This enables incremental debugging and performance tracking.

## 8. Frontend Testing Strategy

### 8.1 Known Issues (from feature‑analysis.md)
- UI integration partial (visualization display).
- Editable equations recomputation pending.
- End‑to‑end testing needed.

### 8.2 Testing Types
- **Component Testing**: Use React Testing Library for individual components.
- **UI Interaction Testing**: Simulate user inputs, button clicks, navigation.
- **Visual Regression**: Ensure LaTeX rendering matches expectations.
- **API Integration**: Mock backend calls to test error handling and loading states.

### 8.3 Tools
- Vitest (already configured in frontend)
- Playwright for browser automation
- Chromatic for visual snapshots (optional)

## 9. Test Execution & Automation

### 9.1 Local Development
```bash
# Run all tests
pytest test/ --cov=backend --cov-report=html

# Run specific suite
pytest test/unit/core/ -v

# Run with generated split problems
python scripts/split_2022.py
pytest test/integration/test_2022_problems.py
```

### 9.2 CI/CD Integration
- Add GitHub Actions workflow to run tests on push.
- Enforce coverage thresholds (fail if below 80%).
- Store test artifacts (reports, screenshots).

### 9.3 Reporting
- Generate a comprehensive report after each run (`test‑results/final_report.md`).
- Include pass/fail counts, coverage summary, and failure details.

## 10. Success Criteria

1. All unit tests pass (green).
2. All integration tests pass.
3. 100% of split 2022 problems produce a correct or plausible answer.
4. Frontend UI works end‑to‑end without console errors.
5. Coverage metrics meet targets.
6. Architecture.md is kept up‑to‑date with each significant change.

## 11. Next Steps

1. **Immediate**:
   - Create the directory structure outlined above.
   - Write splitting script for 2022.md.
   - Add missing unit tests for core modules.

2. **Short‑term**:
   - Run existing tests, catalog failures.
   - Fix broken functionalities.

3. **Long‑term**:
   - Implement E2E UI tests.
   - Set up CI/CD pipeline.

---

*This document will be updated as the testing strategy evolves.*