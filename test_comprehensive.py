#!/usr/bin/env python3
"""
Comprehensive test of MathEngine with sample problems.
"""
import asyncio
import os
import sys
import json
sys.path.insert(0, 'backend')

from dotenv import load_dotenv
load_dotenv('backend/.env')

from api.models import SolveRequest, InputType, LLMProvider
from core.engine import MathEngine
from llm.provider import set_api_keys

# Sample problems from test/sample-text-problems/2022.md
SAMPLE_PROBLEMS = [
    ("Find the area between the parabolas $y^{2}=x$ and $x^{2}=y.$", "calculus"),
    ("Determine whether the complex series $\\Sigma_{n=1}^{\\infty}(\\frac{1}{2^{n}}+\\frac{i}{3^{n}})$ is convergent or not.", "complex_analysis"),
    ("Write down the Maclaurin expansion of the complex function $f(z)=\\frac{1}{1-z^{2}}.$", "complex_analysis"),
    ("Find the integral $\\int_{C}\\frac{z^{2}+2z+2}{z^{2}-1}dz$ where C is the circle $|z|=\\frac{1}{2}.$", "complex_analysis"),
    ("Find the Fourier sine transformation of $f(t)=\\begin{cases}1&;0<t<1\\\\ 0&;t>1\\end{cases}$", "integral_transform"),
    ("Find the minimum value of $z=x+y$ subjected to constraints $-4x+y\\ge4$ and $x,y\\ge0$.", "linear_programming"),
]

async def test_problem(problem_text, category):
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if api_key:
        set_api_keys({'deepseek': api_key})
    engine = MathEngine()
    request = SolveRequest(
        input=problem_text,
        input_type=InputType.LATEX,
        provider=LLMProvider.DEEPSEEK,
        show_steps=True,
        visualize=False,
    )
    print(f"\n=== Testing: {category} ===")
    print(f"Problem: {problem_text[:100]}...")
    try:
        response = await engine.solve(request)
        print(f"Success: {response.success}")
        if response.success:
            print(f"Category: {response.category}")
            print(f"Final answer: {response.final_answer}")
            print(f"Steps: {len(response.steps)}")
            for v in response.verifications:
                print(f"  {v.library}: matches={v.matches}")
        else:
            print(f"Error: {response.error}")
        return response.success
    except Exception as e:
        print(f"Exception: {e}")
        return False

async def main():
    results = []
    for problem, cat in SAMPLE_PROBLEMS:
        success = await test_problem(problem, cat)
        results.append((cat, success))
    print("\n=== Summary ===")
    total = len(results)
    passed = sum(1 for _, s in results if s)
    print(f"Passed: {passed}/{total}")
    for cat, s in results:
        status = "PASS" if s else "FAIL"
        print(f"  {cat}: {status}")

if __name__ == "__main__":
    asyncio.run(main())