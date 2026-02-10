"""
REST API routes for MathEngine.
"""
from __future__ import annotations

import os
import uuid
import shutil
import tempfile

from fastapi import APIRouter, File, UploadFile, HTTPException

from api.models import (
    SolveRequest,
    SolveResponse,
    ChatRequest,
    ChatResponse,
    AnalyzePDFRequest,
    PDFAnalysisResponse,
    APIKeysUpdate,
    LLMProvider,
)
from core.engine import MathEngine
from llm.provider import set_api_keys, get_api_keys, get_llm_provider
from pdf.analyzer import PDFAnalyzer
from scripts.library_manager import ScriptLibrary

router = APIRouter()
engine = MathEngine()
pdf_analyzer = PDFAnalyzer()
script_library = ScriptLibrary()

# In-memory chat histories
_chat_histories: dict[str, list[dict]] = {}


# ── Solve ──────────────────────────────────────────────────────────────



@router.post("/solve", response_model=SolveResponse)
async def solve_problem(request: SolveRequest):
    """Solve a math problem with step-by-step explanation."""
    result = await engine.solve(request)
    return result


# ── Chat ───────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the math tutor."""
    conv_id = request.conversation_id or uuid.uuid4().hex
    history = _chat_histories.get(conv_id, [])

    # Add user message
    history.append({"role": "user", "content": request.message})

    try:
        llm = get_llm_provider(request.provider)
        response = await llm.chat(
            message=request.message,
            context=request.context or "",
            history=history,
        )

        # Add assistant response
        history.append({"role": "assistant", "content": response})
        _chat_histories[conv_id] = history

        has_math = "$" in response or "\\(" in response
        return ChatResponse(
            message=response,
            conversation_id=conv_id,
            has_math=has_math,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── PDF Analysis ───────────────────────────────────────────────────────

@router.post("/pdf/analyze", response_model=PDFAnalysisResponse)
async def analyze_pdf(
    file: UploadFile = File(...),
    provider: str = "gemini",
):
    """Upload and analyze a research paper PDF."""
    # Save uploaded file temporarily
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename or "paper.pdf")

    try:
        with open(tmp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        llm_provider = LLMProvider(provider)
        result = await pdf_analyzer.analyze(tmp_path, llm_provider)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ── API Keys ───────────────────────────────────────────────────────────

@router.post("/settings/keys")
async def update_api_keys(config: APIKeysUpdate):
    """Update LLM API keys."""
    keys = {k.provider.value: k.api_key for k in config.keys}
    set_api_keys(keys)
    return {"success": True, "providers": list(keys.keys())}


@router.get("/keys")
async def get_api_key_status():
    """Get list of configured API keys."""
    keys = get_api_keys()
    env_map = {
        "gemini": "GEMINI_API_KEY",
        "claude": "ANTHROPIC_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "openai": "OPENAI_API_KEY",
    }
    
    configured = []
    for provider, env_var in env_map.items():
        if keys.get(provider) or os.getenv(env_var):
            configured.append(provider)
            
    return {"configured": configured}


# ── Script Library ─────────────────────────────────────────────────────

@router.get("/scripts")
async def list_scripts():
    """List all scripts in the library."""
    return script_library.list_all()


@router.get("/scripts/search")
async def search_scripts(q: str, category: str = ""):
    """Search the script library."""
    return script_library.search(q, category)
