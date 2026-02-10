"""
Abstract LLM provider and factory.
Supports Gemini, Claude, DeepSeek, and OpenAI.
"""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Optional

from api.models import LLMProvider


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def generate(self, prompt: str, system: str = "") -> str:
        """Generate a text response from the LLM."""
        ...

    async def understand_problem(self, problem_latex: str) -> dict[str, Any]:
        """Use LLM to understand a math problem and classify it."""
        prompt = f"""Analyze this math problem and classify it.

Problem (LaTeX): {problem_latex}

Respond ONLY with a JSON object containing:
- "category": one of [algebra, calculus, geometry, trigonometry, statistics, probability, linear_algebra, differential_equations, number_theory, discrete_math, complex_analysis, abstract_algebra, topology, numerical_methods, other]
- "description": a clear text description of what the problem asks
- "key_concepts": list of mathematical concepts involved
- "approach": suggested approach to solve it
- "variables": list of variable names used

JSON only, no other text."""

        response = await self.generate(prompt)
        return self._parse_json(response)

    async def generate_solver_code(
        self, problem_latex: str, understanding: dict[str, Any]
    ) -> str:
        """Generate Python solver code for the problem."""
        prompt = f"""You are a math engine code generator. Generate Python code to solve this math problem.

Problem (LaTeX): {problem_latex}
Category: {understanding.get('category', 'unknown')}
Description: {understanding.get('description', '')}
Approach: {understanding.get('approach', '')}

{f"Use this verified solution template as a guide:\n{understanding['skill_template']}\n" if understanding.get('skill_template') else ""}

REQUIREMENTS:
1. Use sympy as the PRIMARY library (already imported as sp)
2. Available pre-imported: numpy (np), sympy (sp), mpmath, scipy, math
3. Available sympy shortcuts: symbols, Symbol, sqrt, sin, cos, tan, log, exp, pi, E, oo, I, Matrix, integrate, diff, limit, summation, solve, simplify, expand, factor, series, latex, Rational
4. Set `_result` to the final answer
5. Set `_result_latex` to the LaTeX string of the final answer using sp.latex()
6. Set `_steps` to a list of dicts, each with:
   - "description": what this step does
   - "expression": the mathematical expression as string
   - "result": the result of this step as string
   - "latex": LaTeX of this step
   - "code": Python code for this step
7. Each step MUST actually compute something — no placeholder steps
8. Use sympy for symbolic computation, not floating point
9. Do NOT import any additional modules
10. Do NOT use print(), just set the variables

Generate ONLY the Python code, no markdown, no explanation.
The code should be directly executable in the sandbox."""

        response = await self.generate(prompt)
        return self._extract_code(response)

    async def generate_explanation(self, problem: str, solution: str, step: str) -> str:
        """Generate student-friendly explanation for a step."""
        prompt = f"""Explain this math step to a university student in clear, simple terms.

Problem: {problem}
Current step: {step}
Solution so far: {solution}

Be concise but thorough. Use analogies if helpful."""

        return await self.generate(prompt)

    async def chat(self, message: str, context: str = "", history: list[dict] = None) -> str:
        """General chat about math problems."""
        system = """You are MathEngine, a friendly math tutor. Help students understand 
math problems and solutions. Use LaTeX notation when writing equations (wrap in $ for 
inline or $$ for display). Be patient, clear, and encouraging."""

        if context:
            system += f"\n\nCurrent problem context:\n{context}"

        prompt = message
        if history:
            conversation = "\n".join(
                f"{'Student' if m['role'] == 'user' else 'Tutor'}: {m['content']}"
                for m in history[-10:]  # last 10 messages
            )
            prompt = f"Previous conversation:\n{conversation}\n\nStudent: {message}"

        return await self.generate(prompt, system=system)

    @staticmethod
    def _parse_json(response: str) -> dict:
        """Extract JSON from LLM response."""
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return {"category": "other", "description": text}

    @staticmethod
    def _extract_code(response: str) -> str:
        """Extract Python code from LLM response."""
        text = response.strip()
        if "```python" in text:
            text = text.split("```python", 1)[1].rsplit("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].rsplit("```", 1)[0]
        return text.strip()


# ── Provider Implementations ─────────────────────────────────────────

class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider."""

    async def generate(self, prompt: str, system: str = "") -> str:
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            "gemini-2.0-flash",
            system_instruction=system or None,
        )
        response = model.generate_content(prompt)
        return response.text


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider."""

    async def generate(self, prompt: str, system: str = "") -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system or "You are a helpful math assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek provider (OpenAI-compatible API)."""

    async def generate(self, prompt: str, system: str = "") -> str:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system or "You are a helpful math assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 4096,
                },
                timeout=60.0,
            )
            data = response.json()
            return data["choices"][0]["message"]["content"]


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider."""

    async def generate(self, prompt: str, system: str = "") -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system or "You are a helpful math assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4096,
        )
        return response.choices[0].message.content


# ── Factory ───────────────────────────────────────────────────────────

# In-memory key store (in production, use encrypted storage)
_api_keys: dict[str, str] = {}


def set_api_keys(keys: dict[str, str]):
    """Store API keys in memory."""
    global _api_keys
    _api_keys.update(keys)


def get_api_keys() -> dict[str, str]:
    """Get stored API keys."""
    return dict(_api_keys)


def get_llm_provider(
    provider: LLMProvider,
    api_keys: dict[str, str] | None = None,
) -> BaseLLMProvider:
    """Factory: return the correct LLM provider instance."""
    keys = api_keys or _api_keys

    # Also check environment variables
    env_map = {
        LLMProvider.GEMINI: "GEMINI_API_KEY",
        LLMProvider.CLAUDE: "ANTHROPIC_API_KEY",
        LLMProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
        LLMProvider.OPENAI: "OPENAI_API_KEY",
    }

    key = keys.get(provider.value) or os.getenv(env_map.get(provider, ""), "")
    if not key:
        raise ValueError(
            f"No API key configured for {provider.value}. "
            f"Set it via the settings page or the {env_map.get(provider, '')} environment variable."
        )

    providers = {
        LLMProvider.GEMINI: GeminiProvider,
        LLMProvider.CLAUDE: ClaudeProvider,
        LLMProvider.DEEPSEEK: DeepSeekProvider,
        LLMProvider.OPENAI: OpenAIProvider,
    }

    return providers[provider](key)
