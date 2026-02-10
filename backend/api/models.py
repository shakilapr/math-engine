"""
Pydantic models for MathEngine API requests and responses.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────

class InputType(str, Enum):
    LATEX = "latex"
    TEXT = "text"
    IMAGE = "image"


class LLMProvider(str, Enum):
    GEMINI = "gemini"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"
    OPENAI = "openai"


class ProblemCategory(str, Enum):
    ALGEBRA = "algebra"
    CALCULUS = "calculus"
    GEOMETRY = "geometry"
    TRIGONOMETRY = "trigonometry"
    STATISTICS = "statistics"
    PROBABILITY = "probability"
    LINEAR_ALGEBRA = "linear_algebra"
    DIFFERENTIAL_EQUATIONS = "differential_equations"
    NUMBER_THEORY = "number_theory"
    DISCRETE_MATH = "discrete_math"
    COMPLEX_ANALYSIS = "complex_analysis"
    ABSTRACT_ALGEBRA = "abstract_algebra"
    TOPOLOGY = "topology"
    NUMERICAL_METHODS = "numerical_methods"
    OTHER = "other"


# ── Request Models ─────────────────────────────────────────────────────

class SolveRequest(BaseModel):
    input: str = Field(..., description="Problem input (LaTeX, text, or base64 image)")
    input_type: InputType = Field(InputType.TEXT, description="Type of input")
    provider: LLMProvider = Field(LLMProvider.GEMINI, description="LLM provider to use")
    show_steps: bool = Field(True, description="Whether to show step-by-step solution")
    visualize: bool = Field(False, description="Whether to generate visualizations")


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    provider: LLMProvider = Field(LLMProvider.GEMINI)
    context: Optional[str] = None  # previous problem/solution context


class AnalyzePDFRequest(BaseModel):
    provider: LLMProvider = Field(LLMProvider.GEMINI)


class APIKeyConfig(BaseModel):
    provider: LLMProvider
    api_key: str


class APIKeysUpdate(BaseModel):
    keys: list[APIKeyConfig]


# ── Response Models ────────────────────────────────────────────────────

class SolutionStep(BaseModel):
    step_number: int
    description: str = Field(..., description="Student-friendly explanation")
    latex: str = Field(..., description="LaTeX representation of this step")
    python_code: str = Field("", description="Python code that computed this step")
    result: str = Field("", description="Numeric/symbolic result of this step")


class VerificationResult(BaseModel):
    library: str = Field(..., description="Library used for verification")
    result: str
    matches: bool
    code: str = Field("", description="Code used for verification")


class Visualization(BaseModel):
    title: str
    image_url: str
    description: str = ""


class SolveResponse(BaseModel):
    success: bool
    problem_latex: str = Field("", description="Parsed problem in LaTeX")
    category: ProblemCategory = ProblemCategory.OTHER
    steps: list[SolutionStep] = Field(default_factory=list)
    final_answer: str = ""
    final_answer_latex: str = ""
    verifications: list[VerificationResult] = Field(default_factory=list)
    visualizations: list[Visualization] = Field(default_factory=list)
    generated_code: str = Field("", description="Full Python code that was executed")
    error: Optional[str] = None


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    has_math: bool = False
    latex_content: Optional[str] = None


class PDFSection(BaseModel):
    section_title: str
    original_text: str
    math_expressions: list[str] = Field(default_factory=list)
    calculations: list[SolutionStep] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)


class PDFAnalysisResponse(BaseModel):
    success: bool
    filename: str = ""
    total_sections: int = 0
    sections: list[PDFSection] = Field(default_factory=list)
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
