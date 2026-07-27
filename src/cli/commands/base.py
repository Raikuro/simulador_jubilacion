"""Base command contract and execution context."""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionContext:
    verbose: bool = False
    debug: bool = False
    data_dir: str | None = None


class BaseCommand:
    name: str = ""
    help_text: str = ""

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    def execute(self, context: ExecutionContext, args: argparse.Namespace) -> int:
        raise NotImplementedError
