"""
Unit tests for the SelfEditor — core self-evolving capability.

Tests cover:
- File read / write / edit / patch operations
- Path traversal protection (sandbox guard)
- Allowlist enforcement
- AST validation for Python files
- Rollback to previous backup
- Edit history tracking
"""
from __future__ import annotations

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Allow imports from backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from core.self_edit import SelfEditor, PatchHunk


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def workspace(tmp_path: Path):
    """Create a temporary workspace with sample files."""
    # Create directory structure matching allowed patterns
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    api_dir = tmp_path / "api"
    api_dir.mkdir()

    # Sample Python file
    (core_dir / "engine.py").write_text(
        'def solve(problem):\n    """Solve a math problem."""\n    return 42\n',
        encoding="utf-8",
    )

    # Sample script
    (scripts_dir / "helper.py").write_text(
        'import math\n\ndef calculate(x):\n    return math.sqrt(x)\n',
        encoding="utf-8",
    )

    # API file (not in allowed list)
    (api_dir / "routes.py").write_text(
        'from fastapi import APIRouter\nrouter = APIRouter()\n',
        encoding="utf-8",
    )

    # Sensitive file
    (tmp_path / ".env").write_text("SECRET_KEY=abc123\n", encoding="utf-8")

    return tmp_path


@pytest.fixture
def editor(workspace: Path):
    """Create a SelfEditor instance."""
    return SelfEditor(workspace_root=str(workspace))


# ── Read Tests ─────────────────────────────────────────────────────────

class TestReadFile:
    def test_read_existing_file(self, editor: SelfEditor):
        result = editor.read_file("core/engine.py")
        assert "def solve" in result["content"]
        assert result["lines"] > 0
        assert result["path"] == "core/engine.py"

    def test_read_nonexistent_file(self, editor: SelfEditor):
        with pytest.raises(FileNotFoundError):
            editor.read_file("core/missing.py")

    def test_read_path_traversal_blocked(self, editor: SelfEditor, workspace: Path):
        with pytest.raises(PermissionError, match="Path traversal"):
            editor.read_file("../../etc/passwd")

    def test_read_absolute_path_outside_workspace(self, editor: SelfEditor):
        with pytest.raises(PermissionError, match="Path traversal"):
            editor.read_file("/etc/passwd")


# ── Write Tests ────────────────────────────────────────────────────────

class TestWriteFile:
    def test_write_new_file(self, editor: SelfEditor, workspace: Path):
        result = editor.write_file(
            "core/new_module.py",
            "def hello():\n    return 'world'\n",
        )
        assert result.success
        assert (workspace / "core" / "new_module.py").exists()

    def test_write_overwrite_existing(self, editor: SelfEditor, workspace: Path):
        result = editor.write_file(
            "core/engine.py",
            "def solve_v2(problem):\n    return 99\n",
        )
        assert result.success
        assert result.backup_id  # should have created a backup
        content = (workspace / "core" / "engine.py").read_text()
        assert "solve_v2" in content

    def test_write_syntax_error_rejected(self, editor: SelfEditor):
        result = editor.write_file(
            "core/bad.py",
            "def broken(\n    missing end\n",
        )
        assert not result.success
        assert "Syntax" in result.message

    def test_write_disallowed_path(self, editor: SelfEditor):
        with pytest.raises(PermissionError, match="not in allowed"):
            editor.write_file("api/routes.py", "# hacked\n")

    def test_write_denied_path(self, editor: SelfEditor):
        with pytest.raises(PermissionError, match="deny list"):
            editor.write_file(".env", "SECRET=evil\n")

    def test_write_path_traversal(self, editor: SelfEditor):
        with pytest.raises(PermissionError):
            editor.write_file("../../evil.py", "# evil\n")


# ── Edit Tests ─────────────────────────────────────────────────────────

class TestEditFile:
    def test_edit_success(self, editor: SelfEditor, workspace: Path):
        result = editor.edit_file(
            "core/engine.py",
            "return 42",
            "return 99",
        )
        assert result.success
        assert result.diff  # should have a diff
        content = (workspace / "core" / "engine.py").read_text()
        assert "return 99" in content
        assert "return 42" not in content

    def test_edit_old_text_not_found(self, editor: SelfEditor):
        result = editor.edit_file(
            "core/engine.py",
            "nonexistent text here",
            "replacement",
        )
        assert not result.success
        assert "not found" in result.message

    def test_edit_syntax_error_rejected(self, editor: SelfEditor, workspace: Path):
        result = editor.edit_file(
            "core/engine.py",
            "return 42",
            "return 42\n    def broken(",  # introduces syntax error
        )
        assert not result.success
        assert "syntax" in result.message.lower()
        # Original file should be unchanged
        content = (workspace / "core" / "engine.py").read_text()
        assert "return 42" in content

    def test_edit_disallowed_path(self, editor: SelfEditor):
        with pytest.raises(PermissionError):
            editor.edit_file("api/routes.py", "APIRouter", "HackedRouter")

    def test_edit_nonexistent_file(self, editor: SelfEditor):
        with pytest.raises(FileNotFoundError):
            editor.edit_file("core/missing.py", "old", "new")


# ── Patch Tests ────────────────────────────────────────────────────────

class TestApplyPatch:
    def test_patch_add_file(self, editor: SelfEditor, workspace: Path):
        result = editor.apply_patch([
            PatchHunk(
                kind="add",
                path="core/utils.py",
                content="def util():\n    pass\n",
            ),
        ])
        assert result.success
        assert "core/utils.py" in result.added
        assert (workspace / "core" / "utils.py").exists()

    def test_patch_update_file(self, editor: SelfEditor, workspace: Path):
        result = editor.apply_patch([
            PatchHunk(
                kind="update",
                path="core/engine.py",
                old_text="return 42",
                new_text="return 100",
            ),
        ])
        assert result.success
        assert "core/engine.py" in result.modified
        content = (workspace / "core" / "engine.py").read_text()
        assert "return 100" in content

    def test_patch_delete_file(self, editor: SelfEditor, workspace: Path):
        # Create a deletable file first
        (workspace / "scripts" / "to_delete.py").write_text("# temp\n")
        result = editor.apply_patch([
            PatchHunk(kind="delete", path="scripts/to_delete.py"),
        ])
        assert result.success
        assert "scripts/to_delete.py" in result.deleted
        assert not (workspace / "scripts" / "to_delete.py").exists()

    def test_patch_mixed_operations(self, editor: SelfEditor, workspace: Path):
        result = editor.apply_patch([
            PatchHunk(
                kind="add",
                path="core/new.py",
                content="x = 1\n",
            ),
            PatchHunk(
                kind="update",
                path="core/engine.py",
                old_text="return 42",
                new_text="return 0",
            ),
        ])
        assert result.success
        assert len(result.added) == 1
        assert len(result.modified) == 1

    def test_patch_syntax_error_skipped(self, editor: SelfEditor):
        result = editor.apply_patch([
            PatchHunk(
                kind="add",
                path="core/bad.py",
                content="def broken(\n",
            ),
        ])
        assert len(result.errors) > 0


# ── Validation Tests ───────────────────────────────────────────────────

class TestValidation:
    def test_validate_valid_python(self, editor: SelfEditor):
        result = editor.validate_file("core/engine.py")
        assert result.valid

    def test_validate_nonexistent(self, editor: SelfEditor):
        result = editor.validate_file("core/missing.py")
        assert not result.valid

    def test_validate_non_python(self, editor: SelfEditor, workspace: Path):
        (workspace / "scripts" / "data.json").write_text('{"key": "value"}\n')
        result = editor.validate_file("scripts/data.json")
        assert result.valid  # Non-Python files pass validation
        assert any("Not a Python" in w for w in result.warnings)


# ── Rollback Tests ─────────────────────────────────────────────────────

class TestRollback:
    def test_rollback_restores_file(self, editor: SelfEditor, workspace: Path):
        # Read original
        original = (workspace / "core" / "engine.py").read_text()

        # Edit
        result = editor.edit_file("core/engine.py", "return 42", "return 999")
        assert result.success
        backup_id = result.backup_id

        # Verify edit applied
        assert "return 999" in (workspace / "core" / "engine.py").read_text()

        # Rollback
        rb = editor.rollback(backup_id)
        assert rb.success

        # Verify restored
        restored = (workspace / "core" / "engine.py").read_text()
        assert restored == original

    def test_rollback_invalid_id(self, editor: SelfEditor):
        result = editor.rollback("nonexistent_123")
        assert not result.success


# ── History Tests ──────────────────────────────────────────────────────

class TestHistory:
    def test_history_tracks_edits(self, editor: SelfEditor):
        editor.write_file("core/a.py", "x = 1\n")
        editor.edit_file("core/a.py", "x = 1", "x = 2")

        history = editor.get_history()
        assert len(history) == 2
        assert history[0]["operation"] == "edit"  # most recent first
        assert history[1]["operation"] == "write"


# ── List Files Tests ───────────────────────────────────────────────────

class TestListFiles:
    def test_list_python_files(self, editor: SelfEditor):
        files = editor.list_files("**/*.py")
        paths = [f["path"] for f in files]
        assert any("engine.py" in p for p in paths)

    def test_list_marks_editability(self, editor: SelfEditor):
        files = editor.list_files("**/*.py")
        core_files = [f for f in files if f["path"].startswith("core")]
        api_files = [f for f in files if f["path"].startswith("api")]
        # Core files should be editable
        assert all(f["editable"] for f in core_files)
        # API files should NOT be editable
        assert all(not f["editable"] for f in api_files)
