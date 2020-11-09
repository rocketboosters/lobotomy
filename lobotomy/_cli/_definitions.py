import argparse
import dataclasses
import typing


@dataclasses.dataclass(frozen=True)
class CliContext:
    """Data structure for CLI execution context."""

    #: Parsed arguments for the CLI invocation.
    args: argparse.Namespace


@dataclasses.dataclass(frozen=True)
class ExecutionResult:
    """Data structure for a CLI command execution result."""

    #: Exit identifier specifying how the command was resolved.
    code: str
    #: Message for the associated result.
    message: typing.Optional[str] = None

    def echo(self) -> "ExecutionResult":
        """Echoes the result if set for display to the console."""
        print(f"[{self.code}] {self.message}")
        return self
