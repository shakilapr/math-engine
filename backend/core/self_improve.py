"""
Self-Improvement Engine — uses LLM to analyze failures and patch code.

This module orchestrates the self-repair loop:
1. Detect failure in MathEngine.solve()
2. Read relevant source code via SelfEditor
3. Ask LLM to analyze the root cause
4. Ask LLM to generate a patch
5. Validate and apply the patch
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from api.models import LLMProvider
from core.self_edit import SelfEditor, PatchHunk, PatchResult
from llm.provider import get_llm_provider, BaseLLMProvider

logger = logging.getLogger(__name__)


# ── Data Models ────────────────────────────────────────────────────────

@dataclass
class FailureContext:
    """Context for a solver failure."""
    problem_latex: str
    category: str
    error_message: str
    generated_code: str
    stack_trace: str = ""
    provider: LLMProvider = LLMProvider.GEMINI


@dataclass
class ImprovementProposal:
    """Proposed code improvement."""
    analysis: str
    files_to_modify: list[str]
    hunks: list[PatchHunk]
    confidence: str  # "high", "medium", "low"


# ── Prompts ────────────────────────────────────────────────────────────

PROMPT_ANALYZE_FAILURE = """You are a senior Python engineer debugging a math engine.
Analyze this failure and identify the root cause.

Problem: {problem}
Category: {category}
Error: {error}
Code that failed:
```python
{code}
```

Stack Trace:
{trace}

Task:
1. Determine if the error is in the generated solver code OR in the engine's core logic.
2. If it's the engine logic, identify which file likely needs fixing.
3. Be specific about the bug (e.g., "Missing import", "Incorrect SymPy usage", "Sandbox restriction").

Respond ONLY with JSON:
{{
  "cause": "brief explanation",
  "location": "solver_code" or "engine_core",
  "suspected_files": ["core/engine.py", "scripts/algebra.py"],
  "confidence": "high|medium|low"
}}
"""

PROMPT_GENERATE_PATCH = """You are a senior Python engineer. Generate a patch to fix this bug.

Bug Analysis: {analysis}
Target File: {filename}

Current Content of {filename}:
```python
{content}
```

Task:
Generate a unified diff or specific search/replace block to fix the bug.
Prefer minimal changes. Preserving indentation is CRITICAL.

Respond ONLY with JSON:
{{
  "explanation": "what this patch does",
  "hunks": [
    {{
      "kind": "update",
      "path": "{filename}",
      "old_text": "text to be replaced (must match exactly)",
      "new_text": "replacement text"
    }}
  ]
}}
"""


# ── SelfImprover ───────────────────────────────────────────────────────

class SelfImprover:
    """
    Orchestrates the self-improvement loop.
    """

    def __init__(self, editor: SelfEditor):
        self.editor = editor
        # In a real system, we might use a dedicated "coding" model
        self.provider = LLMProvider.GEMINI

    async def analyze_failure(self, context: FailureContext) -> ImprovementProposal | None:
        """
        Analyze a failure and propose a fix.
        Returns code improvement proposal or None if no clear fix found.
        """
        llm = get_llm_provider(self.provider)

        # 1. Analyze Root Cause
        analysis_json = await self._run_analysis(llm, context)
        if not analysis_json:
            return None

        logger.info(f"Failure analysis: {analysis_json}")

        # If error is in generated solver code, we can't "fix" the engine,
        # but we might improve the system prompt (out of scope for now).
        # We only care about "engine_core" errors or recurring script errors.
        if analysis_json.get("location") == "solver_code":
            logger.info("Error is in transient solver code — skipping engine patch.")
            return None

        suspected_files = analysis_json.get("suspected_files", [])
        if not suspected_files:
            return None

        # 2. Read Target Files
        target_file = suspected_files[0]  # Start with the most likely one
        try:
            file_data = self.editor.read_file(target_file)
        except (FileNotFoundError, PermissionError) as e:
            logger.warning(f"Cannot read suspected file {target_file}: {e}")
            return None

        # 3. Generate Patch
        patch_json = await self._generate_patch(
            llm,
            target_file,
            file_data["content"],
            analysis_json["cause"]
        )
        if not patch_json:
            return None

        return self._parse_proposal(patch_json)

    async def apply_proposal(self, proposal: ImprovementProposal) -> PatchResult:
        """
        Apply a validated improvement proposal.
        """
        return self.editor.apply_patch(proposal.hunks)

    # ── Helpers ────────────────────────────────────────────────────────

    async def _run_analysis(self, llm: BaseLLMProvider, context: FailureContext) -> dict | None:
        prompt = PROMPT_ANALYZE_FAILURE.format(
            problem=context.problem_latex,
            category=context.category,
            error=context.error_message,
            code=context.generated_code,
            trace=context.stack_trace,
        )
        response = await llm.generate(prompt)
        return self._parse_json_response(response)

    async def _generate_patch(
        self,
        llm: BaseLLMProvider,
        filename: str,
        content: str,
        analysis: str
    ) -> dict | None:
        prompt = PROMPT_GENERATE_PATCH.format(
            analysis=analysis,
            filename=filename,
            content=content,
        )
        response = await llm.generate(prompt)
        return self._parse_json_response(response)

    def _parse_proposal(self, patch_data: dict) -> ImprovementProposal:
        hunks = []
        for h in patch_data.get("hunks", []):
            hunks.append(PatchHunk(
                kind=h.get("kind", "update"),
                path=h.get("path", ""),
                old_text=h.get("old_text", ""),
                new_text=h.get("new_text", ""),
                content=h.get("content", ""),
            ))

        return ImprovementProposal(
            analysis=patch_data.get("explanation", ""),
            files_to_modify=[h.path for h in hunks],
            hunks=hunks,
            confidence="high",  # dynamic confidence logic could go here
        )

    @staticmethod
    def _parse_json_response(response: str) -> dict | None:
        """Robust JSON extraction from LLM response."""
        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
