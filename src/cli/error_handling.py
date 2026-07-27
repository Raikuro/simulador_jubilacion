"""Exit codes and error formatting."""

from __future__ import annotations

import sys
from enum import IntEnum


class ExitCode(IntEnum):
    SUCCESS = 0
    ERROR = 1
    VALIDATION_ERROR = 2
    INTERRUPTED = 130


def format_error(message: str, exit_code: ExitCode = ExitCode.ERROR) -> str:
    return f"ERROR: {message}"


def handle_exception(exception: Exception) -> int:
    print(format_error(str(exception)), file=sys.stderr)
    return ExitCode.ERROR
