#!/usr/bin/env python3
"""
Detailed test of MathEngine with numbered problems from 2022.md and image problems.
"""
import asyncio
import os
import sys
import re
import base64
import json
from pathlib import Path
sys.path.insert(0, 'backend')

from dotenv import load_dotenv
load_dotenv('backend/.env')

from api.models import SolveRequest, InputType, LLMProvider
from core.engine import MathEngine
from llm.provider import set_api_keys

# Set API key
api_key = os.getenv('DEEPSEEK_API_KEY')
if api_key:
    set_api_keys({'deepseek': api_key})

def extract_questions_from_md(md_path):
    """Extract numbered questions from 2022.md."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Pattern: "Question X: ..." up to next "Question" or end
    # Also handle "Q1", "Q2" etc.
    pattern = r'(?:Question|Q)(?:\s*)(\d+)(?:[:\s]*)(.*?)(?=(?:Question|Q)\s*\d+|\Z)'
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
    questions = []
    for num, text in matches:
        text = text.strip()
        # Remove extra blank lines
        text = re.sub(r'\n\s*\n', '\n', text)
        questions.append({
            'number': int(num),
            'text': text,
            'type': 'latex'
        })
    # If regex fails, fallback to splitting by lines and manual grouping
    if not questions:
        lines = content.split('\n')
        # simple heuristic
        pass
    return questions

def extract_all_problems():
    """Extract all problems from 2022.md including part A and B."""
    with open('test/sample-text-problems/2022.md', 'r', encoding='utf-8') as f:
        content = f.read()
    # Split by "Question X:" pattern
    parts = re.split(r'(?:Question|Q)\s*(\d+)', content)
    # The first part is header, then alternating number and text
    problems = []
    for i in range(1, len(parts), 2):
        num = parts[i]
        text = parts[i+1] if i+1 < len(parts) else ''
        # Clean up
        text = text.strip()
        if not text:
            continue
        # Remove leading colon or space
        text = re.sub(r'^[:\s]+', '', text)
        problems.append({
            'number': int(num),
            'text': text,
            'type': 'latex'
        })
    return problems

def load_image_as_base64(image_path):
    """Read image file and return base64 string."""
    with open(image_path, 'rb') as f:
        image_data = f.read()
    b64 = base64.b64encode(image_data).decode('utf-8')
    # Data URL format
    return f"data:image/png;base64,{b64}"

async def test_problem(engine, problem, category, output_dir):
    """Test a single problem and save results."""
    print(f"\n--- Testing Problem {problem['number']} ({category}) ---")
    print(f"Text: {problem['text'][:200]}...")
    
    if problem['type'] == 'latex':
        request = SolveRequest(
            input=problem['text'],
            input_type=InputType.LATEX,
            provider=LLMProvider.DEEPSEEK,
            show_steps=True,
            visualize=False,
        )
    elif problem['type'] == 'image':
        request = SolveRequest(
            input=problem['image_data'],
            input_type=InputType.IMAGE,
            provider=LLMProvider.DEEPSEEK,
            show_steps=True,
            visualize=False,
        )
    else:
        print(f"Unknown type {problem['type']}")
        return None
    
    try:
        response = await engine.solve(request)
        # Save raw response
        result = {
            'problem_number': problem['number'],
            'category': category,
            'problem_text': problem['text'][:5000] if 'text' in problem else '[image]',
            'success': response.success,
            'category_detected': response.category.value if response.success else None,
            'final_answer': response.final_answer,
            'final_answer_latex': response.final_answer_latex,
            'steps': [
                {
                    'step_number': step.step_number,
                    'description': step.description,
                    'latex': step.latex,
                    'result': step.result,
                    'python_code': step.python_code,
                }
                for step in response.steps
            ],
            'verifications': [
                {
                    'library': v.library,
                    'result': v.result,
                    'matches': v.matches,
                }
                for v in response.verifications
            ],
            'error': response.error,
            'generated_code': response.generated_code[:5000] if response.generated_code else '',
        }
        # Write to JSON
        filename = f"problem_{problem['number']:03d}_{category}.json"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Saved to {filepath}")
        return result
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    output_dir = Path('test/test-results/detailed')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    engine = MathEngine()
    
    # 1. Text problems from 2022.md
    problems = extract_all_problems()
    print(f"Found {len(problems)} text problems.")
    
    results = []
    for prob in problems:
        res = await test_problem(engine, prob, 'text', output_dir)
        if res:
            results.append(res)
    
    # 2. Image problems
    image_dir = Path('test/sample-image-problems')
    if image_dir.exists():
        image_files = list(image_dir.glob('*.png'))
        for idx, img_path in enumerate(image_files, start=1):
            prob = {
                'number': idx,
                'image_data': load_image_as_base64(img_path),
                'type': 'image',
                'text': f'Image {img_path.name}'
            }
            res = await test_problem(engine, prob, 'image', output_dir)
            if res:
                results.append(res)
    
    # Generate summary report
    summary = {
        'total_tested': len(results),
        'successful': sum(1 for r in results if r['success']),
        'failed': sum(1 for r in results if not r['success']),
        'problems': [
            {
                'number': r['problem_number'],
                'category': r['category'],
                'success': r['success'],
                'answer': r['final_answer'][:100] if r['success'] else r['error'],
            }
            for r in results
        ]
    }
    summary_path = output_dir / 'summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n=== Summary ===")
    print(f"Total problems tested: {summary['total_tested']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Detailed results saved in {output_dir}/")
    
    # Also generate a markdown report
    md_path = output_dir / 'detailed_report.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Detailed Test Report\n\n")
        f.write(f"**Date**: {__import__('datetime').datetime.now().isoformat()}\n\n")
        f.write(f"**Total Problems**: {summary['total_tested']}  \n")
        f.write(f"**Successful**: {summary['successful']}  \n")
        f.write(f"**Failed**: {summary['failed']}  \n\n")
        for r in results:
            f.write(f"## Problem {r['problem_number']} ({r['category']})\n")
            f.write(f"**Success**: {r['success']}  \n")
            if r['success']:
                f.write(f"**Answer**: {r['final_answer']}  \n")
                f.write(f"**Steps**: {len(r['steps'])}  \n")
                for step in r['steps']:
                    f.write(f"  {step['step_number']}. {step['description']}  \n")
                f.write(f"**Verifications**: {len(r['verifications'])} matches  \n")
            else:
                f.write(f"**Error**: {r['error']}  \n")
            f.write("\n---\n\n")
    print(f"Markdown report saved to {md_path}")

if __name__ == "__main__":
    asyncio.run(main())