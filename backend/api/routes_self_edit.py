"""
Self-Edit API routes for MathEngine.

Provides endpoints for the LLM agent to read, write, edit, and patch
the project's own source files with safety guards.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from api.models_self_edit import (
    ReadFileRequest,
    ReadFileResponse,
    WriteFileRequest,
    EditFileRequest,
    EditResultResponse,
    ApplyPatchRequest,
    PatchResultResponse,
    RollbackRequest,
    ListFilesRequest,
    FileInfo,
    ValidateFileRequest,
    ValidationResponse,
    HistoryEntry,
    PatchHunkModel,
    ImproveRequest,
    ImprovementProposalResponse,
)
from core.self_edit import SelfEditor, PatchHunk
from core.self_improve import SelfImprover, FailureContext
from api.models import LLMProvider


# ── Singleton editor ───────────────────────────────────────────────────

# Workspace root = backend/ directory
_workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_editor = SelfEditor(workspace_root=_workspace_root)
_improver = SelfImprover(_editor)

router = APIRouter(prefix="/self-edit", tags=["self-edit"])


# ── Read ───────────────────────────────────────────────────────────────

@router.post("/read", response_model=ReadFileResponse)
async def read_file(request: ReadFileRequest):
    """Read a project file's contents."""
    try:
        result = _editor.read_file(request.path)
        return ReadFileResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Write ──────────────────────────────────────────────────────────────

@router.post("/write", response_model=EditResultResponse)
async def write_file(request: WriteFileRequest):
    """Create or overwrite a file (must be in allowed paths)."""
    try:
        result = _editor.write_file(request.path, request.content)
        return EditResultResponse(
            success=result.success,
            path=result.path,
            message=result.message,
            diff=result.diff,
            backup_id=result.backup_id,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Edit ───────────────────────────────────────────────────────────────

@router.post("/edit", response_model=EditResultResponse)
async def edit_file(request: EditFileRequest):
    """Apply a delta edit (oldText → newText)."""
    try:
        result = _editor.edit_file(request.path, request.old_text, request.new_text)
        return EditResultResponse(
            success=result.success,
            path=result.path,
            message=result.message,
            diff=result.diff,
            backup_id=result.backup_id,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ── Patch ──────────────────────────────────────────────────────────────

@router.post("/patch", response_model=PatchResultResponse)
async def apply_patch(request: ApplyPatchRequest):
    """Apply a multi-file patch (add/update/delete)."""
    try:
        hunks = [
            PatchHunk(
                kind=h.kind,
                path=h.path,
                old_text=h.old_text,
                new_text=h.new_text,
                content=h.content,
            )
            for h in request.hunks
        ]
        result = _editor.apply_patch(hunks)
        return PatchResultResponse(
            success=result.success,
            message=result.message,
            added=result.added,
            modified=result.modified,
            deleted=result.deleted,
            errors=result.errors,
            backup_id=result.backup_id,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Validate ───────────────────────────────────────────────────────────

@router.post("/validate", response_model=ValidationResponse)
async def validate_file(request: ValidateFileRequest):
    """Validate a Python file (AST + safety check)."""
    try:
        result = _editor.validate_file(request.path)
        return ValidationResponse(
            valid=result.valid,
            errors=result.errors,
            warnings=result.warnings,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ── Rollback ───────────────────────────────────────────────────────────

@router.post("/rollback", response_model=EditResultResponse)
async def rollback(request: RollbackRequest):
    """Rollback to a previous backup."""
    result = _editor.rollback(request.backup_id)
    if not result.success:
        raise HTTPException(status_code=404, detail=result.message)
    return EditResultResponse(
        success=result.success,
        path=result.path,
        message=result.message,
        backup_id=result.backup_id,
    )


# ── List Files ─────────────────────────────────────────────────────────

@router.post("/list", response_model=list[FileInfo])
async def list_files(request: ListFilesRequest):
    """List files matching a glob pattern."""
    files = _editor.list_files(request.pattern)
    return [FileInfo(**f) for f in files]


# ── History ────────────────────────────────────────────────────────────

@router.get("/history", response_model=list[HistoryEntry])
async def get_history(limit: int = 20):
    """Get recent edit history."""
    entries = _editor.get_history(limit=limit)
    return [HistoryEntry(**e) for e in entries]


# ── Improve ────────────────────────────────────────────────────────────

@router.post("/improve", response_model=ImprovementProposalResponse | None)
async def manual_improve(request: ImproveRequest):
    """Manually trigger self-improvement analysis."""
    context = FailureContext(
        problem_latex=request.problem_latex,
        category=request.category,
        error_message=request.error,
        generated_code=request.code,
        stack_trace=request.traceback,
    )
    # Default to Gemini for now, could become a request field
    proposal = await _improver.analyze_failure(context)
    if not proposal:
        return None

    return ImprovementProposalResponse(
        analysis=proposal.analysis,
        files=proposal.files_to_modify,
        hunks=[
            PatchHunkModel(
                kind=h.kind,
                path=h.path,
                old_text=h.old_text,
                new_text=h.new_text,
                content=h.content
            ) for h in proposal.hunks
        ],
        confidence=proposal.confidence
    )
