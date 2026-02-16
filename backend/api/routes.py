"""
REST API routes for MathEngine.
"""
from __future__ import annotations

import os
import uuid
import shutil
import tempfile

import json
import asyncio
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse

from api.models import (
    SolveRequest,
    SolveResponse,
    ChatRequest,
    ChatResponse,
    AnalyzePDFRequest,
    PDFAnalysisResponse,
    APIKeysUpdate,
    LLMProvider,
    StepCommentRequest,
    SolutionStep,
)
from core.step_orchestrator import StepOrchestrator, StepEvent
from llm.provider import set_api_keys, get_api_keys, get_llm_provider
from pdf.analyzer import PDFAnalyzer
from scripts.library_manager import ScriptLibrary
from scripts.version_control import ScriptVersionControl

router = APIRouter()
orchestrator = StepOrchestrator()
pdf_analyzer = PDFAnalyzer()
script_library = ScriptLibrary()
version_control = ScriptVersionControl()

# In-memory chat histories and solve sessions
_chat_histories: dict[str, list[dict]] = {}
_solve_sessions: dict[str, list[SolutionStep]] = {}


# ── Solve ──────────────────────────────────────────────────────────────


@router.post("/solve")
async def solve_problem(request: SolveRequest, stream: bool = Query(True)):
    """Solve a math problem with step-by-step explanation. Streams granular events."""
    session_id = uuid.uuid4().hex

    if not stream:
        result = await orchestrator.solve(request)
        if result.steps:
            _solve_sessions[session_id] = result.steps
        return {"session_id": session_id, **result.dict()}

    queue: asyncio.Queue = asyncio.Queue()

    async def event_callback(event: StepEvent):
        await queue.put(json.dumps({"type": "step_event", **event.to_dict()}) + "\n")

    async def run_solve():
        try:
            result = await orchestrator.solve(request, event_callback=event_callback)
            if result.steps:
                _solve_sessions[session_id] = result.steps
            await queue.put(json.dumps({
                "type": "result",
                "session_id": session_id,
                "data": result.dict(),
            }) + "\n")
        except Exception as e:
            await queue.put(json.dumps({"type": "error", "message": str(e)}) + "\n")
        finally:
            await queue.put(None)

    async def event_generator():
        task = asyncio.create_task(run_solve())
        try:
            while True:
                data = await queue.get()
                if data is None:
                    break
                yield data
        except asyncio.CancelledError:
             task.cancel()
             raise
        finally:
             await task

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


# ── Step Comment ─────────────────────────────────────────────────────


@router.post("/step/comment")
async def comment_on_step(request: StepCommentRequest):
    """Submit a comment on a specific solution step. LLM reviews and edits the step."""
    session_steps = _solve_sessions.get(request.session_id)
    if not session_steps:
        raise HTTPException(status_code=404, detail="Solve session not found. Solve a problem first.")

    if request.step_index < 0 or request.step_index >= len(session_steps):
        raise HTTPException(status_code=400, detail=f"Step index {request.step_index} out of range")

    edited_step = await orchestrator.comment_on_step(
        session_steps=session_steps,
        step_index=request.step_index,
        comment=request.comment,
        provider=request.provider,
    )

    if edited_step:
        # Update the session
        _solve_sessions[request.session_id][request.step_index] = edited_step
        return {"success": True, "edited_step": edited_step.dict()}
    else:
        return {"success": False, "message": "Failed to process the comment"}


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


# ── Script Library & Catalog ───────────────────────────────────────────

@router.get("/scripts")
async def list_scripts():
    """List all scripts in the library."""
    return script_library.list_all()


@router.get("/scripts/search")
async def search_scripts(q: str, category: str = ""):
    """Search the script library."""
    return script_library.search(q, category)


@router.get("/scripts/catalog")
async def get_catalog():
    """Get the full script catalog grouped by category, for LLM selection."""
    scripts = script_library.list_all()
    catalog: dict[str, list] = {}
    for s in scripts:
        cat = s.get("category", "other")
        catalog.setdefault(cat, []).append({
            "id": s["id"],
            "name": s.get("name", ""),
            "description": s.get("description", ""),
            "tags": s.get("tags", []),
        })
    return {"total": len(scripts), "categories": catalog}


# ── Version Control ────────────────────────────────────────────────────

@router.get("/scripts/versions")
async def list_versioned_scripts():
    """List all scripts with version history."""
    return version_control.list_tracked_scripts()


@router.get("/scripts/{script_id}/history")
async def get_script_history(script_id: str):
    """Get version history for a script."""
    history = version_control.get_history(script_id)
    if not history:
        return {"script_id": script_id, "entries": []}
    from dataclasses import asdict
    return asdict(history)


@router.get("/scripts/{script_id}/version/{version}")
async def get_script_version(script_id: str, version: int):
    """Get the code of a specific version."""
    code = version_control.get_version_code(script_id, version)
    if code is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"script_id": script_id, "version": version, "code": code}


@router.get("/scripts/{script_id}/diff")
async def get_script_diff(script_id: str, v1: int = Query(...), v2: int = Query(...)):
    """Get a diff between two versions of a script."""
    return version_control.get_diff(script_id, v1, v2)


@router.post("/scripts/{script_id}/rollback")
async def rollback_script(script_id: str, target_version: int = Query(...)):
    """Rollback a script to a previous version."""
    # Find the library file path
    for s in script_library.list_all():
        if s.get("id") == script_id:
            import os as _os
            filepath = _os.path.join(
                _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                "scripts", "library", s["filename"]
            )
            success = version_control.rollback(script_id, target_version, filepath)
            if success:
                return {"success": True, "message": f"Rolled back to version {target_version}"}
            raise HTTPException(status_code=400, detail="Rollback failed")
    raise HTTPException(status_code=404, detail="Script not found")
