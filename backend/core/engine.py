"""
MathEngine Core — Main solver pipeline.

Orchestrates: input parsing → LLM code generation → execution →
step-by-step breakdown → cross-verification → visualization.
"""
from __future__ import annotations

import json
import logging
import os
import traceback
from typing import Optional

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
from core.self_edit import SelfEditor
from core.self_improve import SelfImprover, FailureContext
from input.parser import InputParser
from llm.provider import get_llm_provider
from scripts.library_manager import ScriptLibrary
from skills.registry import SkillRegistry


logger = logging.getLogger(__name__)


class MathEngine:
    """Top-level orchestrator for solving math problems."""

    def __init__(self):
        self.executor = SafeExecutor()
        self.verifier = CrossVerifier()
        self.explainer = StepExplainer()
        self.visualizer = MathVisualizer()

        self.parser = InputParser()
        self.script_library = ScriptLibrary()

        # Initialize Self-Evolution components
        workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.editor = SelfEditor(workspace_root)
        self.improver = SelfImprover(self.editor)
        
        # Initialize Skills System
        self.skills = SkillRegistry(workspace_root)
        self.skills.load_all_skills()

    async def solve(
        self, 
        request: SolveRequest, 
        api_keys: dict[str, str] | None = None,
        progress_callback = None
    ) -> SolveResponse:
        """Full pipeline: parse → understand → generate code → execute → explain → verify."""
        try:
            async def report(status: str):
                if progress_callback:
                    await progress_callback(status)

            # 1. Parse input to LaTeX
            await report("Parsing input...")
            problem_latex = await self._parse_input(request)

            # 2. Use LLM to understand problem and generate Python code
            await report("Understanding problem...")
            llm = get_llm_provider(request.provider, api_keys=api_keys)

            if not llm:
                 raise ValueError("LLM provider not initialized")

            understanding = await llm.understand_problem(problem_latex)
            category = understanding.get("category", "other")
            try:
                problem_category = ProblemCategory(category)
            except ValueError:
                problem_category = ProblemCategory.OTHER

            # 2.2 Check for applicable Skill
            skill = self.skills.find_skill(problem_latex)
            if skill:
                logger.info(f"Matched skill: {skill.name}")
                understanding["skill_template"] = skill.template
                # Append skill info to description to help LLM know we are guiding it
                understanding["description"] = (
                    f"{understanding.get('description', '')}\n[Using skill: {skill.name}]"
                )

            # 2.5 Try to find a matching script in library
            library_script = self._try_find_library_script(problem_category, problem_latex, understanding)
            if library_script:
                solver_code = library_script
                source = "library"
            else:
                # 3. Generate solver code via LLM
                await report("Generating solution code...")
                solver_code = await llm.generate_solver_code(problem_latex, understanding)
                source = "llm"

            # 4. Execute the generated code in sandbox
            await report("Executing code...")
            exec_result = self.executor.execute(solver_code)
            if not exec_result["success"]:
                # Attempt self-improvement loop
                try:
                    await report("Analyzing failure...")
                    logger.info("Execution failed — triggering self-improvement analysis")
                    context = FailureContext(
                        problem_latex=problem_latex,
                        category=category,
                        error_message=exec_result.get('error', 'Unknown error'),
                        generated_code=solver_code,
                        stack_trace=exec_result.get('traceback', ''),
                        provider=request.provider
                    )
                    proposal = await self.improver.analyze_failure(context)
                    if proposal:
                        logger.info(f"Self-improvement proposed: {proposal.analysis}")
                except Exception as e:
                    logger.error(f"Self-improvement loop failed: {e}")

                return SolveResponse(
                    success=False,
                    problem_latex=problem_latex,
                    category=problem_category,
                    generated_code=solver_code,
                    error=f"Code execution failed: {exec_result['error']}",
                )

            final_answer = str(exec_result.get("result", ""))
            steps_raw = exec_result.get("steps", [])

            # 5. Generate step-by-step explanations via LLM
            await report("Generating explanations...")
            steps: list[SolutionStep] = []
            if request.show_steps and steps_raw:
                steps = await self.explainer.explain_steps(
                    llm, problem_latex, steps_raw
                )
            elif request.show_steps:
                # Generate steps from the solver code and final answer
                steps = await self.explainer.explain_from_code(
                    llm, problem_latex, solver_code, final_answer
                )

            # 6. Cross-verify with multiple libraries
            await report("Verifying result...")
            verifications = self.verifier.verify(problem_latex, final_answer, solver_code)

            # 7. Add the solved script to library (if it came from LLM)
            if source == "llm":
                # Generate a name from description or problem latex
                name = understanding.get("description", problem_latex)[:80]
                if not name.strip():
                    name = f"Solve {problem_category.value}"
                description = understanding.get("description", problem_latex)
                # Use key concepts as tags
                tags = understanding.get("key_concepts", [])
                # Ensure tags are strings
                tags = [str(tag) for tag in tags]
                # Add primary script
                try:
                    self.script_library.add_script(
                        name=name,
                        description=description,
                        code=solver_code,
                        category=problem_category.value,
                        tags=tags,
                    )
                except Exception as e:
                    # Log but don't fail the request
                    logger.error(f"Failed to add script to library: {e}")

            # 8. Generate visualizations if requested
            visualizations: list[Visualization] = []
            if request.visualize:
                await report("Generating visualization...")
                visualizations = self.visualizer.generate(
                    problem_latex, solver_code, exec_result
                )
            
            await report("Done!")
            return SolveResponse(
                success=True,
                problem_latex=problem_latex,
                category=problem_category,
                steps=steps,
                final_answer=final_answer,
                final_answer_latex=exec_result.get("result_latex", final_answer),
                verifications=verifications,
                visualizations=visualizations,
                generated_code=solver_code,
            )

        except Exception as e:
            traceback.print_exc()
            return SolveResponse(
                success=False,
                error=str(e),
            )

    def _try_find_library_script(
        self,
        category: ProblemCategory,
        problem_latex: str,
        understanding: dict,
    ) -> str | None:
        """Try to find a library script matching the problem."""
        # Search by category
        results = self.script_library.search(query=category.value, category=category.value)
        if not results:
            # Fallback: search by key concepts from understanding
            key_concepts = understanding.get("key_concepts", [])
            for concept in key_concepts[:3]:
                if concept:
                    results = self.script_library.search(query=concept, category="")
                    if results:
                        break
        if not results:
            # Try generic search with problem description
            description = understanding.get("description", "")
            if description:
                words = description.split()[:5]
                for word in words:
                    results = self.script_library.search(query=word, category="")
                    if results:
                        break
        if results:
            # Load the first matching script
            script_id = results[0].get("id")
            return self.script_library.get_script(script_id)
        return None

    async def _parse_input(self, request: SolveRequest) -> str:
        """Convert any input format to LaTeX."""
        if request.input_type == InputType.LATEX:
            return request.input
        elif request.input_type == InputType.TEXT:
            return self.parser.text_to_latex(request.input)
        elif request.input_type == InputType.IMAGE:
            return await self.parser.image_to_latex(request.input)
        return request.input
