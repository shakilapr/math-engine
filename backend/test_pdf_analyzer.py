#!/usr/bin/env python3
"""
Test PDF analyzer pipeline with sample PDF.
"""
import asyncio
import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env')

from pdf.analyzer import PDFAnalyzer
from api.models import LLMProvider

async def test_pdf():
    analyzer = PDFAnalyzer()
    pdf_path = "../test/sample-research-papers/11 RRT Guided Model Predictive Path Integral Method.pdf"
    if not os.path.exists(pdf_path):
        pdf_path = "test/sample-research-papers/11 RRT Guided Model Predictive Path Integral Method.pdf"
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        return
    
    print(f"Analyzing {os.path.basename(pdf_path)}...")
    response = await analyzer.analyze(
        pdf_path=pdf_path,
        provider=LLMProvider.DEEPSEEK,
        api_keys={'deepseek': os.getenv('DEEPSEEK_API_KEY', '')}
    )
    
    print(f"Success: {response.success}")
    if response.success:
        print(f"Total sections: {response.total_sections}")
        for i, section in enumerate(response.sections[:2]):  # first 2
            print(f"Section {i}: {section.title}")
            print(f"  Math expressions: {len(section.math_expressions)}")
            print(f"  Calculations: {len(section.calculations)}")
            if section.calculations:
                for calc in section.calculations[:1]:
                    print(f"    - {calc.description}")
    else:
        print(f"Error: {response.error}")

if __name__ == "__main__":
    asyncio.run(test_pdf())