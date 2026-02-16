"""
Step Orchestrator — Modular step-based solver pipeline.

Instead of generating one monolithic solver, the LLM selects
per-step scripts from the catalog and chains them together.
Each step is streamed to the client in real-time.
"""
from __future__ import annotations

import json
import logging
import traceback
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable, Awaitable

from api.models import (
    InputType,
    LLMProvider,
    ProblemCategory,
    SolveRequest,
    SolveResponse,
    SolutionStep,
    VerificationResult,
    Visualization,
)
from core.executor import SafeExecutor
from core.verifier import CrossVerifier
from core.explainer import StepExplainer
from core.visualizer import MathVisualizer
from input.parser import InputParser
from llm.provider import get_llm_provider
from scripts.library_manager import ScriptLibrary
from scripts.version_control import ScriptVersionControl
from skills.registry import SkillRegistry

logger = logging.getLogger(__name__)


@dataclass
class StepEvent:
    """A granular event emitted during step-by-step solving."""
    type: str  # thinking, script_selected, code_writing, executing, step_result, step_edited, error
    step_index: int = -1
    status: str = ""
    script_id: str = ""
    script_name: str = ""
    code: str = ""
    result: str = ""
    thinking: str = ""
    diff: str = ""
    description: str = ""
    latex: str = ""

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v or k == "step_index"}


# Type alias for the event callback
EventCallback = Callable[[StepEvent], Awaitable[None]]


PLAN_PROMPT = """You are a math problem solver. Given a math problem and a catalog of available
step scripts, create a step-by-step plan to solve it.

## Problem
{problem}

## Understanding
Category: {category}
Description: {description}

## Available Step Scripts (select by ID)
{catalog}

## Instructions
Return a JSON array of steps. Each step should be:
- If using an existing script: {{"action": "use_script", "script_id": "...", "script_name": "...", "description": "what this step does", "input_params": {{...}}}}
- If no suitable script exists: {{"action": "generate", "description": "what this step does", "step_code": "...python code for this single step..."}}

The code for each generated step MUST:
- Use `from sympy import *` and define `x, y, z = symbols('x y z')` as needed
- Set `_result` to the step's output
- Set `_steps` to a list of step descriptions (optional)
- Be self-contained for this ONE step

Return ONLY the JSON array, no other text.
"""

COMMENT_PROMPT = """A user has commented on step {step_index} of a math solution.

## Original Step
Description: {step_description}
Code: {step_code}
Result: {step_result}

## User Comment
{comment}

## Instructions
Based on the user's feedback, provide a corrected/improved version of this step.
Return JSON: {{"description": "...", "step_code": "...python code...", "explanation": "what changed and why"}}
Return ONLY the JSON, no other text.
"""


class StepOrchestrator:
    """
    Orchestrates solving by selecting and chaining per-step scripts.
    
    Flow:
    1. Parse input → understand problem
    2. LLM sees script catalog → plans steps (selects scripts or generates new ones)
    3. Execute each step in sequence, streaming events
    4. Cross-verify final result
    5. Auto-add any generated steps as new scripts
    """

    def __init__(self):
        self.executor = SafeExecutor()
        self.verifier = CrossVerifier()
        self.explainer = StepExplainer()
        self.visualizer = MathVisualizer()
        self.parser = InputParser()
        self.script_library = ScriptLibrary()
        self.version_control = ScriptVersionControl()

        import os
        workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.skills = SkillRegistry(workspace_root)
        self.skills.load_all_skills()

    async def solve(
        self,
        request: SolveRequest,
        api_keys: dict[str, str] | None = None,
        event_callback: EventCallback | None = None,
    ) -> SolveResponse:
        """Full step-by-step pipeline with granular event streaming."""
        try:
            async def emit(event: StepEvent):
                if event_callback:
                    await event_callback(event)

            # 1. Parse input
            await emit(StepEvent(type="thinking", thinking="Parsing input..."))
            problem_latex = await self._parse_input(request)

            # 2. Understand problem
            await emit(StepEvent(type="thinking", thinking="Understanding the problem..."))
            llm = get_llm_provider(request.provider, api_keys=api_keys)
            if not llm:
                raise ValueError("LLM provider not initialized")

            understanding = await llm.understand_problem(problem_latex)
            category = understanding.get("category", "other")
            try:
                problem_category = ProblemCategory(category)
            except ValueError:
                problem_category = ProblemCategory.OTHER

            await emit(StepEvent(
                type="thinking",
                thinking=f"Problem category: {category}. {understanding.get('description', '')}",
            ))

            # 3. Build catalog for LLM
            catalog = self.script_library.list_all()
            catalog_text = self._format_catalog(catalog)

            # 4. LLM plans the steps
            await emit(StepEvent(type="thinking", thinking="Planning solution steps..."))
            plan_prompt = PLAN_PROMPT.format(
                problem=problem_latex,
                category=category,
                description=understanding.get("description", ""),
                catalog=catalog_text,
            )

            plan_response = await llm.chat(
                message=plan_prompt,
                context="You are a math solver planner. Return only valid JSON.",
                history=[],
            )

            steps_plan = self._parse_plan(plan_response)
            if not steps_plan:
                # Fallback: generate a single monolithic step
                await emit(StepEvent(type="thinking", thinking="Generating single-step solution..."))
                solver_code = await llm.generate_solver_code(problem_latex, understanding)
                steps_plan = [{"action": "generate", "description": "Complete solution", "step_code": solver_code}]

            # 5. Execute each step
            solved_steps: list[SolutionStep] = []
            accumulated_code = ""
            final_result = ""

            for idx, step_plan in enumerate(steps_plan):
                step_num = idx + 1

                if step_plan.get("action") == "use_script":
                    script_id = step_plan.get("script_id", "")
                    script_name = step_plan.get("script_name", "")
                    await emit(StepEvent(
                        type="script_selected",
                        step_index=idx,
                        script_id=script_id,
                        script_name=script_name,
                        status=f"Selected script: {script_name}",
                    ))
                    code = self.script_library.get_script(script_id)
                    if not code:
                        # Script not found, generate it
                        await emit(StepEvent(
                            type="code_writing",
                            step_index=idx,
                            status="Script not found, generating...",
                        ))
                        code = step_plan.get("step_code", "")
                        if not code:
                            code = await llm.generate_solver_code(
                                problem_latex,
                                {**understanding, "specific_step": step_plan.get("description", "")},
                            )
                else:
                    # Generate step code
                    code = step_plan.get("step_code", "")
                    await emit(StepEvent(
                        type="code_writing",
                        step_index=idx,
                        code=code,
                        status=f"Writing code for step {step_num}...",
                    ))

                # Execute
                await emit(StepEvent(
                    type="executing",
                    step_index=idx,
                    code=code,
                    status=f"Executing step {step_num}...",
                ))

                exec_result = self.executor.execute(code)
                step_result = str(exec_result.get("result", "")) if exec_result["success"] else ""
                step_error = exec_result.get("error", "") if not exec_result["success"] else ""

                # Build explanation
                description = step_plan.get("description", f"Step {step_num}")

                step = SolutionStep(
                    step_number=step_num,
                    description=description,
                    latex="",
                    python_code=code,
                    result=step_result or step_error,
                )
                solved_steps.append(step)

                await emit(StepEvent(
                    type="step_result",
                    step_index=idx,
                    result=step_result or step_error,
                    description=description,
                    code=code,
                    status=f"Step {step_num} {'completed' if exec_result['success'] else 'failed'}",
                ))

                if exec_result["success"]:
                    accumulated_code += f"\n# Step {step_num}: {description}\n{code}\n"
                    final_result = step_result

                # Auto-add generated scripts to library
                if step_plan.get("action") == "generate" and exec_result["success"] and code.strip():
                    try:
                        script_id = self.script_library.add_script(
                            name=description[:80],
                            description=description,
                            code=code,
                            category=category,
                            tags=understanding.get("key_concepts", [])[:5],
                        )
                        self.version_control.commit(
                            script_id, description[:80], code,
                            message=f"Auto-added from solving: {problem_latex[:60]}",
                        )
                    except Exception as e:
                        logger.error(f"Failed to save step script: {e}")

            # 6. Generate explanations via LLM for each step
            await emit(StepEvent(type="thinking", thinking="Generating explanations..."))
            if request.show_steps and solved_steps:
                try:
                    steps_raw = [
                        {"description": s.description, "result": s.result, "code": s.python_code}
                        for s in solved_steps
                    ]
                    explained = await self.explainer.explain_steps(llm, problem_latex, steps_raw)
                    # Merge explanations back
                    for i, exp_step in enumerate(explained):
                        if i < len(solved_steps):
                            solved_steps[i].description = exp_step.description
                            solved_steps[i].latex = exp_step.latex
                except Exception as e:
                    logger.error(f"Explanation generation failed: {e}")

            # 7. Cross-verify
            await emit(StepEvent(type="thinking", thinking="Verifying result..."))
            verifications = self.verifier.verify(problem_latex, final_result, accumulated_code)

            # 8. Visualizations
            visualizations: list[Visualization] = []
            if request.visualize:
                await emit(StepEvent(type="thinking", thinking="Generating visualizations..."))
                exec_result_for_vis = {"result": final_result, "success": True}
                visualizations = self.visualizer.generate(problem_latex, accumulated_code, exec_result_for_vis)

            await emit(StepEvent(type="thinking", thinking="Done!"))

            return SolveResponse(
                success=True,
                problem_latex=problem_latex,
                category=problem_category,
                steps=solved_steps,
                final_answer=final_result,
                final_answer_latex=final_result,
                verifications=verifications,
                visualizations=visualizations,
                generated_code=accumulated_code,
            )

        except Exception as e:
            traceback.print_exc()
            return SolveResponse(success=False, error=str(e))

    async def comment_on_step(
        self,
        session_steps: list[SolutionStep],
        step_index: int,
        comment: str,
        provider: LLMProvider = LLMProvider.GEMINI,
        api_keys: dict[str, str] | None = None,
        event_callback: EventCallback | None = None,
    ) -> SolutionStep | None:
        """Process a user comment on a specific step. Returns the edited step."""
        if step_index < 0 or step_index >= len(session_steps):
            return None

        step = session_steps[step_index]
        llm = get_llm_provider(provider, api_keys=api_keys)
        if not llm:
            return None

        async def emit(event: StepEvent):
            if event_callback:
                await event_callback(event)

        await emit(StepEvent(
            type="thinking",
            step_index=step_index,
            thinking=f"Reviewing your comment on step {step_index + 1}...",
        ))

        prompt = COMMENT_PROMPT.format(
            step_index=step_index + 1,
            step_description=step.description,
            step_code=step.python_code,
            step_result=step.result,
            comment=comment,
        )

        response = await llm.chat(
            message=prompt,
            context="You are a math tutor reviewing student feedback on a solution step.",
            history=[],
        )

        try:
            # Parse the LLM response
            response_clean = response.strip()
            if response_clean.startswith("```"):
                response_clean = response_clean.split("\n", 1)[1].rsplit("```", 1)[0]
            edit_data = json.loads(response_clean)

            new_code = edit_data.get("step_code", step.python_code)
            new_description = edit_data.get("description", step.description)

            # Execute the new code
            await emit(StepEvent(
                type="step_edited",
                step_index=step_index,
                code=new_code,
                description=new_description,
                diff=edit_data.get("explanation", ""),
                status=f"Editing step {step_index + 1}...",
            ))

            exec_result = self.executor.execute(new_code)
            new_result = str(exec_result.get("result", "")) if exec_result["success"] else step.result

            return SolutionStep(
                step_number=step.step_number,
                description=new_description,
                latex=step.latex,
                python_code=new_code,
                result=new_result,
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse comment response: {e}")
            return None

    def _format_catalog(self, scripts: list[dict]) -> str:
        """Format the script catalog for the LLM prompt."""
        if not scripts:
            return "(No scripts available — generate all steps)"
        lines = []
        for s in scripts:
            lines.append(
                f"- ID: {s['id']} | Name: {s.get('name', 'unnamed')} | "
                f"Category: {s.get('category', 'other')} | "
                f"Tags: {', '.join(s.get('tags', []))}"
            )
        return "\n".join(lines)

    def _parse_plan(self, response: str) -> list[dict]:
        """Parse the LLM's step plan from JSON."""
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            parsed = json.loads(clean)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, IndexError):
            logger.warning(f"Failed to parse step plan, trying to extract JSON array")
            # Try to find a JSON array in the response
            import re
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return []

    async def _parse_input(self, request: SolveRequest) -> str:
        """Convert any input format to LaTeX."""
        if request.input_type == InputType.LATEX:
            return request.input
        elif request.input_type == InputType.TEXT:
            return self.parser.text_to_latex(request.input)
        elif request.input_type == InputType.IMAGE:
            return await self.parser.image_to_latex(request.input)
        return request.input
