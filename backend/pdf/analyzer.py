"""
PDF research paper extractor and math analyzer.
Extracts mathematical content from PDFs and computes/explains each part.
"""
from __future__ import annotations

import os
import re
import traceback
from typing import Any

from api.models import (
    PDFAnalysisResponse,
    PDFSection,
    SolutionStep,
    LLMProvider,
)
from core.executor import SafeExecutor
from llm.provider import get_llm_provider


class PDFAnalyzer:
    """Extract and analyze mathematical content from research papers."""

    def __init__(self):
        self.executor = SafeExecutor()

    async def analyze(
        self,
        pdf_path: str,
        provider: LLMProvider,
        api_keys: dict[str, str] | None = None,
    ) -> PDFAnalysisResponse:
        """Full PDF analysis pipeline."""
        try:
            # 1. Extract text and math from PDF
            sections = self._extract_sections(pdf_path)
            filename = os.path.basename(pdf_path)

            # 2. For each section, identify math, compute, and explain
            llm = get_llm_provider(provider, api_keys=api_keys)
            analyzed_sections: list[PDFSection] = []

            for section in sections:
                analyzed = await self._analyze_section(section, llm)
                analyzed_sections.append(analyzed)

            return PDFAnalysisResponse(
                success=True,
                filename=filename,
                total_sections=len(analyzed_sections),
                sections=analyzed_sections,
            )
        except Exception as e:
            traceback.print_exc()
            return PDFAnalysisResponse(
                success=False,
                error=str(e),
            )

    def _extract_sections(self, pdf_path: str) -> list[dict[str, str]]:
        """Extract text sections from PDF."""
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(pdf_path)
            sections = []
            current_section = {"title": "Introduction", "text": ""}

            for page in doc:
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if "lines" not in block:
                        continue
                    for line in block["lines"]:
                        text = ""
                        max_size = 0
                        for span in line["spans"]:
                            text += span["text"]
                            max_size = max(max_size, span["size"])

                        text = text.strip()
                        if not text:
                            continue

                        # Detect section headings (larger font or numbered)
                        if max_size > 12 and len(text) < 100:
                            if current_section["text"].strip():
                                sections.append(current_section)
                            current_section = {"title": text, "text": ""}
                        else:
                            current_section["text"] += text + "\n"

            if current_section["text"].strip():
                sections.append(current_section)

            doc.close()
            return sections

        except ImportError:
            # Fallback to pdfplumber
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += (page.extract_text() or "") + "\n"

            # Split by common section patterns
            parts = re.split(
                r"\n(?=\d+\.?\s+[A-Z]|\n[A-Z][A-Z\s]+\n)",
                full_text,
            )
            return [
                {"title": f"Section {i + 1}", "text": part}
                for i, part in enumerate(parts)
                if part.strip()
            ]

    def _extract_math_expressions(self, text: str) -> list[str]:
        """Pull LaTeX math expressions from text."""
        patterns = [
            r"\$\$(.+?)\$\$",   # Display math
            r"\$(.+?)\$",       # Inline math
            r"\\begin\{equation\}(.+?)\\end\{equation\}",
            r"\\begin\{align\}(.+?)\\end\{align\}",
            r"\\[(.+?)\\]",
        ]
        expressions = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            expressions.extend(matches)
        return expressions

    async def _analyze_section(
        self, section: dict[str, str], llm
    ) -> PDFSection:
        """Analyze a single section for math content."""
        text = section["text"]
        math_exprs = self._extract_math_expressions(text)

        calculations: list[SolutionStep] = []
        explanations: list[str] = []

        if math_exprs:
            # Use LLM to generate explanation and computation code
            prompt = f"""Analyze these mathematical expressions from a research paper section.

Section title: {section['title']}
Context: {text[:1000]}

Math expressions found:
{chr(10).join(f'  {i+1}. {e}' for i, e in enumerate(math_exprs))}

For each expression:
1. Explain what it represents in simple terms
2. If it can be computed/verified, provide the computation

Respond as JSON with:
- "explanations": list of strings explaining each expression
- "can_compute": list of booleans indicating if each can be computed

JSON only."""

            response = await llm.generate(prompt)
            try:
                import json
                parsed = json.loads(
                    response.strip().strip("`").replace("```json", "").replace("```", "")
                )
                explanations = parsed.get("explanations", [])
            except Exception:
                explanations = [f"Expression: {e}" for e in math_exprs]

        return PDFSection(
            section_title=section["title"],
            original_text=text[:2000],  # Truncate for response size
            math_expressions=math_exprs,
            calculations=calculations,
            explanations=explanations,
        )
