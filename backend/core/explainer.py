"""
Step-by-step explanation generator.
Uses LLM to create student-friendly explanations for each solution step.
"""
from __future__ import annotations

from typing import Any

from api.models import SolutionStep


class StepExplainer:
    """Generate student-friendly step-by-step explanations."""

    async def explain_steps(
        self,
        llm,
        problem_latex: str,
        steps_raw: list[dict[str, Any]],
    ) -> list[SolutionStep]:
        """Take raw execution steps and add student-friendly explanations."""
        if not steps_raw:
            return []

        # Format steps for LLM
        steps_text = ""
        for i, step in enumerate(steps_raw, 1):
            steps_text += f"Step {i}: {step.get('description', '')}\n"
            steps_text += f"  Expression: {step.get('expression', '')}\n"
            steps_text += f"  Result: {step.get('result', '')}\n\n"

        prompt = f"""You are a patient math tutor explaining a solution to a student.

Problem (LaTeX): {problem_latex}

Here are the computation steps:
{steps_text}

For each step, provide:
1. A clear, student-friendly explanation of WHAT is being done and WHY
2. The LaTeX representation of the step

Respond as a JSON array of objects with keys:
- "step_number": int
- "description": string (student-friendly explanation)
- "latex": string (LaTeX of this step)

Be detailed but clear. Explain concepts like you would to a university student.
Respond ONLY with the JSON array, no other text."""

        response = await llm.generate(prompt)
        return self._parse_steps_response(response, steps_raw)

    async def explain_from_code(
        self,
        llm,
        problem_latex: str,
        solver_code: str,
        final_answer: str,
    ) -> list[SolutionStep]:
        """Generate step-by-step explanation from the solver code and final answer."""
        prompt = f"""You are a patient math tutor. Break down the following solution into clear steps.

Problem (LaTeX): {problem_latex}
Final Answer: {final_answer}

Python code that solved it:
```python
{solver_code}
```

Break this into logical mathematical steps. For each step, provide:
1. A student-friendly explanation
2. The LaTeX for that step
3. The Python code for that specific step
4. The intermediate result

Respond as a JSON array of objects with keys:
- "step_number": int
- "description": string
- "latex": string
- "python_code": string
- "result": string

Be thorough. A student should be able to follow these steps and understand the complete solution.
Respond ONLY with the JSON array, no other text."""

        response = await llm.generate(prompt)
        return self._parse_full_steps_response(response)

    def _parse_steps_response(
        self, response: str, steps_raw: list[dict]
    ) -> list[SolutionStep]:
        """Parse LLM response into SolutionStep objects."""
        import json

        try:
            # Extract JSON from response
            text = response.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]

            data = json.loads(text)
            steps = []
            for i, item in enumerate(data):
                raw = steps_raw[i] if i < len(steps_raw) else {}
                steps.append(SolutionStep(
                    step_number=item.get("step_number", i + 1),
                    description=item.get("description", raw.get("description", "")),
                    latex=item.get("latex", raw.get("latex", "")),
                    python_code=raw.get("code", ""),
                    result=str(raw.get("result", "")),
                ))
            return steps
        except (json.JSONDecodeError, Exception):
            # Fallback: use raw steps without LLM explanations
            return [
                SolutionStep(
                    step_number=i + 1,
                    description=s.get("description", f"Step {i + 1}"),
                    latex=s.get("latex", str(s.get("expression", ""))),
                    python_code=s.get("code", ""),
                    result=str(s.get("result", "")),
                )
                for i, s in enumerate(steps_raw)
            ]

    def _parse_full_steps_response(self, response: str) -> list[SolutionStep]:
        """Parse LLM full steps response."""
        import json

        try:
            text = response.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]

            data = json.loads(text)
            return [
                SolutionStep(
                    step_number=item.get("step_number", i + 1),
                    description=item.get("description", ""),
                    latex=item.get("latex", ""),
                    python_code=item.get("python_code", ""),
                    result=str(item.get("result", "")),
                )
                for i, item in enumerate(data)
            ]
        except (json.JSONDecodeError, Exception):
            return [
                SolutionStep(
                    step_number=1,
                    description="Solution computed (explanation unavailable)",
                    latex="",
                    python_code="",
                    result="",
                )
            ]
