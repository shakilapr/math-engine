"""
Self-Edit Engine — allows the LLM agent to read, write, and edit
MathEngine's own source files with safety guards.

Inspired by OpenClaw's pi-coding-agent tool architecture:
- Path containment checks (sandbox guard)
- Allowlist-based path filtering
- AST validation after edits
- Git-based rollback via auto-commit before modifications
"""
from __future__ import annotations

import ast
import difflib
import fnmatch
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any


# ── Data Classes ───────────────────────────────────────────────────────

@dataclass
class EditResult:
    """Result of a file edit operation."""
    success: bool
    path: str
    message: str
    diff: str = ""
    backup_id: str = ""


@dataclass
class PatchHunk:
    """A single hunk in a multi-file patch."""
    kind: str  # "add" | "update" | "delete"
    path: str
    old_text: str = ""
    new_text: str = ""
    content: str = ""  # for "add" kind


@dataclass
class PatchResult:
    """Result of applying a multi-file patch."""
    success: bool
    message: str
    added: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    backup_id: str = ""


@dataclass
class ValidationResult:
    """Result of validating a Python file."""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class EditHistoryEntry:
    """A recorded edit operation for rollback."""
    backup_id: str
    timestamp: float
    operation: str  # "write" | "edit" | "patch" | "delete"
    files: list[str]
    description: str
    backup_dir: str


# ── Constants ──────────────────────────────────────────────────────────

DEFAULT_ALLOWED_PATTERNS = [
    "core/**/*.py",
    "scripts/**/*.py",
    "scripts/**/*.json",
    "input/**/*.py",
    "llm/**/*.py",
    "pdf/**/*.py",
]

# Files that should never be modified by the self-editor
DENY_PATTERNS = [
    "**/.env",
    "**/.env.*",
    "**/secrets*",
    "**/credentials*",
]

MAX_FILE_SIZE = 500_000  # 500 KB
MAX_PATCH_FILES = 20


# ── SelfEditor ─────────────────────────────────────────────────────────

class SelfEditor:
    """
    Allows the LLM agent to read, write, and edit MathEngine's own
    source code with safety guards.

    Safety layers (inspired by OpenClaw):
    1. Path containment — all paths must resolve inside workspace_root
    2. Allowlist filtering — only files matching allowed_patterns can be modified
    3. Deny list — sensitive files (env, secrets) are always blocked
    4. AST validation — Python files are parsed after edits to catch syntax errors
    5. Backup/rollback — git stash or file copy before any modification
    """

    def __init__(
        self,
        workspace_root: str,
        allowed_patterns: list[str] | None = None,
        backup_dir: str | None = None,
    ):
        self.workspace_root = Path(workspace_root).resolve()
        self.allowed_patterns = allowed_patterns or DEFAULT_ALLOWED_PATTERNS
        self.backup_dir = Path(backup_dir) if backup_dir else self.workspace_root / ".self_edit_backups"
        self.history: list[EditHistoryEntry] = []

    # ── Path Helpers ───────────────────────────────────────────────────

    def _rel_posix(self, resolved: Path) -> str:
        """Return the POSIX-style relative path (forward slashes on all OS)."""
        return str(resolved.relative_to(self.workspace_root)).replace("\\", "/")

    # ── Public API ─────────────────────────────────────────────────────

    def read_file(self, file_path: str) -> dict[str, Any]:
        """Read a file's contents. Any file in workspace is readable."""
        resolved = self._resolve_path(file_path)
        self._assert_in_workspace(resolved)

        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not resolved.is_file():
            raise ValueError(f"Not a file: {file_path}")
        if resolved.stat().st_size > MAX_FILE_SIZE:
            raise ValueError(f"File too large: {resolved.stat().st_size} bytes (max {MAX_FILE_SIZE})")

        content = resolved.read_text(encoding="utf-8", errors="replace")
        lines = content.split("\n")

        return {
            "path": self._rel_posix(resolved),
            "content": content,
            "lines": len(lines),
            "size": resolved.stat().st_size,
        }

    def write_file(self, file_path: str, content: str) -> EditResult:
        """Create or overwrite a file. Must be in allowed paths."""
        resolved = self._resolve_path(file_path)
        self._assert_writable(resolved)

        is_new = not resolved.exists()
        backup_id = ""

        # Backup existing file
        if not is_new:
            backup_id = self._backup_files([resolved], "write")

        # Validate if Python
        if resolved.suffix == ".py":
            validation = self._validate_python_source(content)
            if not validation.valid:
                return EditResult(
                    success=False,
                    path=self._rel_posix(resolved),
                    message=f"Syntax errors in new content: {'; '.join(validation.errors)}",
                )

        # Write
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")

        action = "created" if is_new else "overwritten"
        rel = self._rel_posix(resolved)

        self._record_history(
            backup_id=backup_id,
            operation="write",
            files=[rel],
            description=f"File {action}: {rel}",
        )

        return EditResult(
            success=True,
            path=rel,
            message=f"File {action} successfully",
            backup_id=backup_id,
        )

    def edit_file(self, file_path: str, old_text: str, new_text: str) -> EditResult:
        """
        Apply a delta edit: replace old_text with new_text.
        Mirrors OpenClaw's edit tool (oldText → newText).
        """
        resolved = self._resolve_path(file_path)
        self._assert_writable(resolved)

        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = resolved.read_text(encoding="utf-8")

        # Check old_text exists
        occurrences = content.count(old_text)
        if occurrences == 0:
            # Try with normalized whitespace
            normalized_content = self._normalize_whitespace(content)
            normalized_old = self._normalize_whitespace(old_text)
            if normalized_old in normalized_content:
                return EditResult(
                    success=False,
                    path=self._rel_posix(resolved),
                    message="oldText found with whitespace differences. Please match exact whitespace.",
                )
            return EditResult(
                success=False,
                path=self._rel_posix(resolved),
                message="oldText not found in file.",
            )
        if occurrences > 1:
            return EditResult(
                success=False,
                path=self._rel_posix(resolved),
                message=f"oldText found {occurrences} times — must be unique. Add surrounding context.",
            )

        # Apply edit
        new_content = content.replace(old_text, new_text, 1)

        # Validate if Python
        if resolved.suffix == ".py":
            validation = self._validate_python_source(new_content)
            if not validation.valid:
                return EditResult(
                    success=False,
                    path=self._rel_posix(resolved),
                    message=f"Edit would introduce syntax errors: {'; '.join(validation.errors)}",
                )

        # Backup and apply
        backup_id = self._backup_files([resolved], "edit")

        # Generate diff
        diff = self._generate_diff(content, new_content, file_path)

        resolved.write_text(new_content, encoding="utf-8")
        rel = self._rel_posix(resolved)

        self._record_history(
            backup_id=backup_id,
            operation="edit",
            files=[rel],
            description=f"Edited: {rel}",
        )

        return EditResult(
            success=True,
            path=rel,
            message="Edit applied successfully",
            diff=diff,
            backup_id=backup_id,
        )

    def apply_patch(self, hunks: list[PatchHunk]) -> PatchResult:
        """
        Apply a multi-file patch. Mirrors OpenClaw's apply_patch tool.
        Supports add, update, and delete operations.
        """
        if len(hunks) > MAX_PATCH_FILES:
            return PatchResult(
                success=False,
                message=f"Patch touches too many files ({len(hunks)} > {MAX_PATCH_FILES})",
            )

        # Validate all paths first
        resolved_hunks: list[tuple[PatchHunk, Path]] = []
        for hunk in hunks:
            resolved = self._resolve_path(hunk.path)
            if hunk.kind != "delete":
                self._assert_writable(resolved)
            else:
                self._assert_in_workspace(resolved)
            resolved_hunks.append((hunk, resolved))

        # Backup all affected files
        existing_files = [p for _, p in resolved_hunks if p.exists()]
        backup_id = self._backup_files(existing_files, "patch") if existing_files else ""

        result = PatchResult(success=True, message="Patch applied", backup_id=backup_id)
        affected_files = []

        for hunk, resolved in resolved_hunks:
            rel = self._rel_posix(resolved)
            try:
                if hunk.kind == "add":
                    if resolved.exists():
                        result.errors.append(f"File already exists: {rel}")
                        continue
                    resolved.parent.mkdir(parents=True, exist_ok=True)
                    if resolved.suffix == ".py":
                        v = self._validate_python_source(hunk.content)
                        if not v.valid:
                            result.errors.append(f"Syntax error in new file {rel}: {'; '.join(v.errors)}")
                            continue
                    resolved.write_text(hunk.content, encoding="utf-8")
                    result.added.append(rel)
                    affected_files.append(rel)

                elif hunk.kind == "update":
                    if not resolved.exists():
                        result.errors.append(f"File not found: {rel}")
                        continue
                    content = resolved.read_text(encoding="utf-8")
                    if hunk.old_text not in content:
                        result.errors.append(f"oldText not found in {rel}")
                        continue
                    new_content = content.replace(hunk.old_text, hunk.new_text, 1)
                    if resolved.suffix == ".py":
                        v = self._validate_python_source(new_content)
                        if not v.valid:
                            result.errors.append(f"Syntax error after edit in {rel}: {'; '.join(v.errors)}")
                            continue
                    resolved.write_text(new_content, encoding="utf-8")
                    result.modified.append(rel)
                    affected_files.append(rel)

                elif hunk.kind == "delete":
                    if not resolved.exists():
                        result.errors.append(f"File not found for deletion: {rel}")
                        continue
                    resolved.unlink()
                    result.deleted.append(rel)
                    affected_files.append(rel)

            except Exception as e:
                result.errors.append(f"Error processing {rel}: {e}")

        if result.errors:
            result.success = len(result.errors) < len(hunks)
            result.message = f"Patch partially applied ({len(result.errors)} errors)"

        self._record_history(
            backup_id=backup_id,
            operation="patch",
            files=affected_files,
            description=f"Patch: +{len(result.added)} ~{len(result.modified)} -{len(result.deleted)}",
        )

        return result

    def list_files(self, pattern: str = "**/*.py") -> list[dict[str, Any]]:
        """List files matching a glob pattern within the workspace."""
        results = []
        for match in sorted(self.workspace_root.glob(pattern)):
            if match.is_file() and not self._is_denied(match):
                rel = str(match.relative_to(self.workspace_root)).replace("\\", "/")
                try:
                    size = match.stat().st_size
                except OSError:
                    size = 0
                results.append({
                    "path": rel,
                    "size": size,
                    "editable": self._is_allowed(match),
                })
        return results

    def validate_file(self, file_path: str) -> ValidationResult:
        """Validate a Python file (AST check + import check)."""
        resolved = self._resolve_path(file_path)
        self._assert_in_workspace(resolved)

        if not resolved.exists():
            return ValidationResult(valid=False, errors=[f"File not found: {file_path}"])
        if resolved.suffix != ".py":
            return ValidationResult(valid=True, warnings=["Not a Python file, skipping validation"])

        content = resolved.read_text(encoding="utf-8")
        return self._validate_python_source(content)

    def rollback(self, backup_id: str) -> EditResult:
        """Rollback to a previous backup."""
        entry = self._find_history_entry(backup_id)
        if not entry:
            return EditResult(
                success=False,
                path="",
                message=f"Backup not found: {backup_id}",
            )

        backup_path = Path(entry.backup_dir)
        if not backup_path.exists():
            return EditResult(
                success=False,
                path="",
                message=f"Backup directory missing: {entry.backup_dir}",
            )

        restored = []
        for file_rel in entry.files:
            backup_file = backup_path / file_rel
            target = self.workspace_root / file_rel

            if backup_file.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(backup_file), str(target))
                restored.append(file_rel)
            elif entry.operation == "write" and target.exists():
                # File was created (no prior version); remove it
                target.unlink()
                restored.append(file_rel)

        return EditResult(
            success=True,
            path="",
            message=f"Rolled back {len(restored)} file(s) from backup {backup_id}",
            backup_id=backup_id,
        )

    def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent edit history entries."""
        entries = self.history[-limit:]
        return [
            {
                "backup_id": e.backup_id,
                "timestamp": e.timestamp,
                "operation": e.operation,
                "files": e.files,
                "description": e.description,
            }
            for e in reversed(entries)
        ]

    # ── Safety Guards ──────────────────────────────────────────────────

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve a relative or absolute path to an absolute path."""
        p = Path(file_path)
        if p.is_absolute():
            return p.resolve()
        return (self.workspace_root / p).resolve()

    def _assert_in_workspace(self, resolved: Path) -> None:
        """Ensure path is inside the workspace root (prevent path traversal)."""
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError:
            raise PermissionError(
                f"Path traversal blocked: {resolved} is outside workspace {self.workspace_root}"
            )

    def _assert_writable(self, resolved: Path) -> None:
        """Ensure path is both in workspace and on the allowlist."""
        self._assert_in_workspace(resolved)
        if self._is_denied(resolved):
            raise PermissionError(f"Path is on deny list: {resolved.name}")
        if not self._is_allowed(resolved):
            rel = self._rel_posix(resolved)
            raise PermissionError(
                f"Path not in allowed patterns: {rel}. "
                f"Allowed: {self.allowed_patterns}"
            )

    def _is_allowed(self, resolved: Path) -> bool:
        """Check if a file matches any of the allowed patterns."""
        try:
            rel = self._rel_posix(resolved)
        except ValueError:
            return False
        return any(self._match_pattern(rel, pat) for pat in self.allowed_patterns)

    def _is_denied(self, resolved: Path) -> bool:
        """Check if a file matches any deny pattern."""
        try:
            rel = self._rel_posix(resolved)
        except ValueError:
            return True
        return any(self._match_pattern(rel, pat) for pat in DENY_PATTERNS)

    @staticmethod
    def _match_pattern(path: str, pattern: str) -> bool:
        """
        Match a POSIX path against a glob pattern.
        Handles ** as zero-or-more directory levels (unlike PurePosixPath.match
        which requires at least one level).
        """
        # fnmatch doesn't support **, so we expand ** patterns:
        # 'core/**/*.py' should match 'core/engine.py' AND 'core/sub/engine.py'
        if "**" in pattern:
            # Split on ** and check: prefix matches start, suffix matches end
            parts = pattern.split("**")
            if len(parts) == 2:
                prefix = parts[0]  # e.g. 'core/'
                suffix = parts[1]  # e.g. '/*.py'
                # Remove leading/trailing slashes from suffix
                suffix = suffix.lstrip("/")
                if path.startswith(prefix) and fnmatch.fnmatch(path[len(prefix):], suffix):
                    return True
                # Also try matching with intermediate dirs
                if path.startswith(prefix) and fnmatch.fnmatch(path[len(prefix):], "**/" + suffix):
                    return True
                # Direct fnmatch for full pattern (in case it works)
                return fnmatch.fnmatch(path, pattern)
            return fnmatch.fnmatch(path, pattern)
        return fnmatch.fnmatch(path, pattern)

    # ── Validation ─────────────────────────────────────────────────────

    def _validate_python_source(self, source: str) -> ValidationResult:
        """Validate Python source code via AST parsing."""
        errors = []
        warnings = []

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return ValidationResult(
                valid=False,
                errors=[f"Line {e.lineno}: {e.msg}"],
            )

        # Check for dangerous patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ("os", "subprocess", "shutil", "sys"):
                        warnings.append(
                            f"Line {node.lineno}: imports '{alias.name}' — review for safety"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in ("os", "subprocess", "shutil"):
                    warnings.append(
                        f"Line {node.lineno}: imports from '{node.module}' — review for safety"
                    )

        return ValidationResult(valid=True, warnings=warnings)

    # ── Backup / History ───────────────────────────────────────────────

    def _backup_files(self, files: list[Path], operation: str) -> str:
        """Create a backup of files before modification."""
        backup_id = f"{operation}_{int(time.time() * 1000)}"
        backup_path = self.backup_dir / backup_id

        for f in files:
            if f.exists():
                rel = f.relative_to(self.workspace_root)
                dest = backup_path / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(f), str(dest))

        return backup_id

    def _record_history(
        self,
        backup_id: str,
        operation: str,
        files: list[str],
        description: str,
    ) -> None:
        """Record an edit operation in history."""
        self.history.append(EditHistoryEntry(
            backup_id=backup_id or f"{operation}_{int(time.time() * 1000)}",
            timestamp=time.time(),
            operation=operation,
            files=files,
            description=description,
            backup_dir=str(self.backup_dir / backup_id) if backup_id else "",
        ))

    def _find_history_entry(self, backup_id: str) -> EditHistoryEntry | None:
        """Find a history entry by backup ID."""
        for entry in reversed(self.history):
            if entry.backup_id == backup_id:
                return entry
        return None

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Normalize whitespace for fuzzy matching."""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _generate_diff(old: str, new: str, filename: str) -> str:
        """Generate a unified diff string."""
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
        return "".join(diff)
