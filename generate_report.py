#!/usr/bin/env python3
"""
Generate comprehensive markdown report from detailed test results.
"""
import json
import os
import glob
from pathlib import Path

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    detailed_dir = Path('test/test-results/detailed')
    if not detailed_dir.exists():
        print("Detailed results not found.")
        return
    
    # Load summary
    summary_path = detailed_dir / 'summary.json'
    if summary_path.exists():
        summary = load_json(summary_path)
    else:
        summary = {'total_tested': 0, 'successful': 0, 'failed': 0, 'problems': []}
    
    # Collect all JSON files (excluding summary)
    json_files = list(detailed_dir.glob('problem_*.json'))
    # Sort by problem number and category
    json_files.sort(key=lambda p: (p.stem.split('_')[1], p.stem.split('_')[2]))
    
    # Load each
    problems = []
    for f in json_files:
        data = load_json(f)
        problems.append(data)
    
    # Generate markdown
    md_path = detailed_dir / 'COMPREHENSIVE_REPORT.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# MathEngine Comprehensive Test Report\n\n")
        f.write(f"**Date**: {__import__('datetime').datetime.now().isoformat()}\n")
        f.write(f"**Total Problems Tested**: {summary['total_tested']}  \n")
        f.write(f"**Successful**: {summary['successful']}  \n")
        f.write(f"**Failed**: {summary['failed']}  \n\n")
        
        f.write("## Table of Contents\n")
        f.write("- [Text Problems (2022.md)](#text-problems-2022md)\n")
        f.write("- [Image Problems](#image-problems)\n")
        f.write("- [Failure Analysis](#failure-analysis)\n")
        f.write("- [Recommendations](#recommendations)\n\n")
        
        # Text problems
        f.write("## Text Problems (2022.md)\n\n")
        text_probs = [p for p in problems if p['category'] == 'text']
        text_probs.sort(key=lambda p: p['problem_number'])
        for prob in text_probs:
            f.write(f"### Problem {prob['problem_number']}\n")
            f.write(f"**Status**: {'✅ PASS' if prob['success'] else '❌ FAIL'}  \n")
            f.write(f"**Category Detected**: {prob.get('category_detected', 'N/A')}  \n")
            f.write(f"**Problem Statement**:  \n")
            text_snippet = prob['problem_text'][:500].replace('\n', '  \n> ')
            f.write(f"> {text_snippet}  \n")
            if prob['success']:
                f.write(f"**Final Answer**: {prob['final_answer']}  \n")
                f.write(f"**Final Answer (LaTeX)**: {prob['final_answer_latex']}  \n")
                f.write(f"**Number of Steps**: {len(prob['steps'])}  \n")
                f.write("**Steps**:  \n")
                for step in prob['steps']:
                    f.write(f"{step['step_number']}. **{step['description']}**  \n")
                    if step['latex']:
                        f.write(f"   LaTeX: `{step['latex']}`  \n")
                    if step['result']:
                        f.write(f"   Result: `{step['result']}`  \n")
                    f.write("\n")
                f.write(f"**Verifications**:  \n")
                for v in prob['verifications']:
                    f.write(f"- {v['library']}: matches={v['matches']}  \n")
            else:
                f.write(f"**Error**: {prob.get('error', 'Unknown error')}  \n")
            f.write("\n---\n\n")
        
        # Image problems
        f.write("## Image Problems\n\n")
        image_probs = [p for p in problems if p['category'] == 'image']
        image_probs.sort(key=lambda p: p['problem_number'])
        for prob in image_probs:
            f.write(f"### Image {prob['problem_number']}\n")
            f.write(f"**Status**: {'✅ PASS' if prob['success'] else '❌ FAIL'}  \n")
            f.write(f"**File**: {prob['problem_text']}  \n")
            if prob['success']:
                f.write(f"**Final Answer**: {prob['final_answer']}  \n")
                f.write(f"**Steps**: {len(prob['steps'])}  \n")
            else:
                f.write(f"**Error**: {prob.get('error', 'Unknown error')}  \n")
                # Common error due to torch DLL
                if 'torch' in prob.get('error', '').lower() or 'dll' in prob.get('error', '').lower():
                    f.write("> **Note**: Image-to-LaTeX conversion failed due to PyTorch DLL issue on Windows. This is a system dependency problem, not a bug in MathEngine.\n")
            f.write("\n---\n\n")
        
        # Failure analysis
        f.write("## Failure Analysis\n\n")
        failures = [p for p in problems if not p['success']]
        if failures:
            f.write("| Problem | Category | Error |\n")
            f.write("|---------|----------|-------|\n")
            for p in failures:
                f.write(f"| {p['problem_number']} ({p['category']}) | {p.get('category_detected', 'N/A')} | {p.get('error', '')[:100]} |\n")
            f.write("\n")
        else:
            f.write("No failures! 🎉\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        f.write("1. **Fix Image Processing**: Resolve PyTorch DLL issue by reinstalling torch with compatible CUDA version or using CPU-only build.\n")
        f.write("2. **Improve LLM Prompts**: Some problems (e.g., linear programming) generate code with type errors. Enhance prompt engineering for those categories.\n")
        f.write("3. **Expand Script Library**: Populate `backend/scripts/library/` with template solvers for common problem types to improve speed and reliability.\n")
        f.write("4. **UI Integration**: Start frontend dev server (`bun run dev`) and test end-to-end workflow.\n")
        f.write("5. **Add More Verification Libraries**: Include Sage, CVXOPT, or other specialized math libraries for broader coverage.\n")
        f.write("\n")
        f.write("---\n")
        f.write("*Generated by MathEngine test automation.*\n")
    
    print(f"Report generated at {md_path}")
    print(f"Total problems processed: {len(problems)}")

if __name__ == '__main__':
    main()