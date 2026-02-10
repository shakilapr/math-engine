"""
Pydantic models for the Self-Edit API.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ── Request Models ─────────────────────────────────────────────────────

class ReadFileRequest(BaseModel):
    path: str = Field(..., description="Relative path to the file within the workspace")


class WriteFileRequest(BaseModel):
    path: str = Field(..., description="Relative path to create or overwrite")
    content: str = Field(..., description="Full file content to write")


class EditFileRequest(BaseModel):
    path: str = Field(..., description="Relative path to the file to edit")
    old_text: str = Field(..., description="Exact text to find and replace (must be unique)")
    new_text: str = Field(..., description="Replacement text")


class PatchHunkModel(BaseModel):
    kind: str = Field(..., description="Operation: 'add', 'update', or 'delete'")
    path: str = Field(..., description="Relative file path")
    old_text: str = Field("", description="Text to replace (for 'update' kind)")
    new_text: str = Field("", description="Replacement text (for 'update' kind)")
    content: str = Field("", description="Full content (for 'add' kind)")


class ApplyPatchRequest(BaseModel):
    hunks: list[PatchHunkModel] = Field(..., description="List of patch hunks to apply")


class RollbackRequest(BaseModel):
    backup_id: str = Field(..., description="Backup ID to rollback to")


class ListFilesRequest(BaseModel):
    pattern: str = Field("**/*.py", description="Glob pattern to filter files")


class ValidateFileRequest(BaseModel):
    path: str = Field(..., description="Relative path to the Python file to validate")


class ImproveRequest(BaseModel):
    problem_latex: str = Field(..., description="Problem that caused failure")
    category: str = Field("other", description="Problem category")
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Failed code")
    traceback: str = Field("", description="Stack trace")


# ── Response Models ────────────────────────────────────────────────────

class ReadFileResponse(BaseModel):
    path: str
    content: str
    lines: int
    size: int


class EditResultResponse(BaseModel):
    success: bool
    path: str
    message: str
    diff: str = ""
    backup_id: str = ""


class PatchResultResponse(BaseModel):
    success: bool
    message: str
    added: list[str] = Field(default_factory=list)
    modified: list[str] = Field(default_factory=list)
    deleted: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    backup_id: str = ""


class FileInfo(BaseModel):
    path: str
    size: int
    editable: bool


class ValidationResponse(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ImprovementProposalResponse(BaseModel):
    analysis: str
    files: list[str]
    hunks: list[PatchHunkModel]
    confidence: str


class HistoryEntry(BaseModel):
    backup_id: str
    timestamp: float
    operation: str
    files: list[str]
    description: str
