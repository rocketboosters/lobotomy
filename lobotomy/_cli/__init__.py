import typing

from lobotomy._cli import _adder
from lobotomy._cli import _definitions
from lobotomy._cli import _parsing


def run(arguments: typing.List[str] = None) -> "_definitions.ExecutionResult":
    """
    Execute a cli command with the given arguments.

    Defaults to sys.argv if no explicit arguments were specified.
    """
    args = _parsing.parse(arguments)
    context = _definitions.CliContext(args)

    commands = {
        "add": _adder.run,
    }

    return commands[args.command](context)
