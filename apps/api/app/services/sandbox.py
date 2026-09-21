"""Sandboxed code execution.

What is enforced here: a clean temporary working directory, a stripped
environment, a wall-clock timeout, a CPU-time limit, an address-space limit, no
new files outside the temp directory that survive the run, and truncated output.

What is NOT enforced here: network isolation and kernel-level syscall filtering.
Those come from the runtime the API is deployed in. The provided Docker Compose
runs the API in a container; for untrusted multi-tenant code, run the API (or a
dedicated executor service) with `--network none` and a read-only root
filesystem. This limitation is documented, not hidden: `/api/v1/coding/status`
reports it to the UI.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass

from app.core.config import settings

LANGUAGES: dict[str, dict[str, object]] = {
    "python": {"label": "Python 3", "filename": "main.py", "command": [sys.executable, "main.py"]},
    "javascript": {"label": "Node.js", "filename": "main.js", "command": ["node", "main.js"]},
}


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    language: str


class ExecutionUnavailableError(RuntimeError):
    """The requested runtime is not installed or execution is disabled."""


def _limits() -> object:
    """Best-effort resource limits. POSIX only; ignored where unsupported."""
    try:
        import resource
    except ImportError:  # pragma: no cover - non-POSIX
        return None

    cpu = settings.code_execution_timeout_seconds
    memory = settings.code_execution_memory_mb * 1024 * 1024

    def apply() -> None:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
        resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
        resource.setrlimit(resource.RLIMIT_FSIZE, (5 * 1024 * 1024, 5 * 1024 * 1024))
        try:
            resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        except (ValueError, OSError):
            pass
        os.setsid()

    return apply


def runtime_available(language: str) -> bool:
    spec = LANGUAGES.get(language)
    if spec is None:
        return False
    command = spec["command"]  # type: ignore[index]
    executable = command[0]  # type: ignore[index]
    return bool(shutil.which(executable) or os.path.exists(executable))


def run_code(language: str, source: str, stdin: str = "") -> ExecutionResult:
    if not settings.code_execution_enabled:
        raise ExecutionUnavailableError(
            "Code execution is disabled. Set CODE_EXECUTION_ENABLED=true to enable it."
        )
    spec = LANGUAGES.get(language)
    if spec is None:
        raise ExecutionUnavailableError(
            f"Unsupported language '{language}'. Supported: {', '.join(LANGUAGES)}."
        )
    if not runtime_available(language):
        raise ExecutionUnavailableError(
            f"The {spec['label']} runtime is not installed in this container, so "
            f"{language} cannot be executed here."
        )

    timeout = settings.code_execution_timeout_seconds
    with tempfile.TemporaryDirectory(prefix="unios-exec-") as workdir:
        path = os.path.join(workdir, str(spec["filename"]))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(source)

        try:
            completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
                list(spec["command"]),  # type: ignore[arg-type]
                cwd=workdir,
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": workdir},
                preexec_fn=_limits(),  # noqa: PLW1509
            )
        except subprocess.TimeoutExpired as exc:
            return ExecutionResult(
                stdout=_truncate(exc.stdout or ""),
                stderr=f"Execution stopped after {timeout}s (time limit).",
                exit_code=124,
                timed_out=True,
                language=language,
            )

    return ExecutionResult(
        stdout=_truncate(completed.stdout),
        stderr=_truncate(completed.stderr),
        exit_code=completed.returncode,
        timed_out=False,
        language=language,
    )


def _truncate(text: str) -> str:
    limit = settings.code_execution_max_output_chars
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n… output truncated at {limit} characters."
