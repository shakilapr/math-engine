#!/usr/bin/env python3
"""
Quick test of MathEngine pipeline.
"""
import asyncio
import os
import sys
sys.path.insert(0, 'backend')

from dotenv import load_dotenv
load_dotenv('backend/.env')

from api.models import SolveRequest, InputType, LLMProvider
from core.engine import MathEngine
from llm.provider import set_api_keys

async def test_simple():
    # Set API key from environment
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if api_key:
        set_api_keys({'deepseek': api_key})
    engine = MathEngine()
    request = SolveRequest(
        input="solve x^2 - 4 = 0",
        input_type=InputType.TEXT,
        provider=LLMProvider.DEEPSEEK,
        show_steps=True,
        visualize=False,
    )
    # Use existing API key from .env
    response = await engine.solve(request)
    print(f"Success: {response.success}")
    print(f"Category: {response.category}")
    print(f"Final answer: {response.final_answer}")
    print(f"Steps: {len(response.steps)}")
    for step in response.steps:
        print(f"  Step {step.step_number}: {step.description}")
    print(f"Verifications: {len(response.verifications)}")
    for v in response.verifications:
        print(f"  {v.library}: {v.result} (matches: {v.matches})")
    if response.error:
        print(f"Error: {response.error}")

if __name__ == "__main__":
    asyncio.run(test_simple())