import json
import pathlib
import typing

import toml
import yaml

from lobotomy import _fio
from lobotomy import _mutator
from lobotomy import _services
from lobotomy._cli import _definitions


def _get_path(
    context: "_definitions.CliContext",
) -> typing.Optional[pathlib.Path]:
    if context.args.configuration_file_path in [None, "-"]:
        return None

    return pathlib.Path(context.args.configuration_file_path).expanduser().absolute()


def run(context: "_definitions.CliContext") -> "_definitions.ExecutionResult":
    """Adds a new call to the specified command actions."""
    file_format = context.args.file_format
    path = _get_path(context)
    prefix = [item for item in (context.args.prefix or "").split(".") if item]

    try:
        configs = _fio.read(path, prefix, file_format=file_format)  # type: ignore
    except (AttributeError, FileNotFoundError, TypeError):
        configs = {}

    service_name, method_name = context.args.boto_operation.split(".")
    service = _services.load_definition(service_name)
    method = service.lookup(method_name)

    _mutator.add_service_response(configs, method)

    if path:
        _fio.write(path, configs, prefix, file_format=file_format)
        return _definitions.ExecutionResult(
            code="ADDED", message="New call has been added to the configs."
        ).echo()

    if file_format == "json":
        print(json.dumps(configs, indent=2))
    elif file_format == "toml":
        print(toml.dumps(configs))
    else:
        print(yaml.dump(configs))

    return _definitions.ExecutionResult(
        code="ECHOED", message="New call has been echoed to stdout."
    )
