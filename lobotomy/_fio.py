import json
import pathlib
import typing

import toml
import yaml


def _read_file(path: pathlib.Path, file_format: str = None) -> dict:
    """Reads the configuration file from disk if it exists."""
    p = pathlib.Path(path).expanduser().absolute()
    if not p.exists():
        return {}

    contents = p.read_text()

    if file_format == "yaml" or path.name.endswith((".yaml", ".yml")):
        return yaml.safe_load(contents)

    if file_format == "toml" or path.name.endswith(".toml"):
        return typing.cast(dict, toml.loads(contents))

    return json.loads(contents)


def read(
    path: typing.Union[str, pathlib.Path],
    prefix: typing.Union[str, typing.Iterable[str]] = None,
    file_format: str = None,
) -> typing.Dict[str, typing.Any]:
    """
    Reads the specified configuration file and returns the result. If a
    prefix is specified, the data at the given prefix will be returned
    instead.

    :param path:
        Path to the configuration file to read.
    :param prefix:
        Optional prefix within the file in which the configuration resides.
    :param file_format:
        Optional format for the file, which will be determined from the
        file extension if omitted.
    :return:
        A dictionary containing the lobotomy configuration data from the
        given file. This will be an empty dictionary if no configuration
        exists yet.
    """
    data = _read_file(pathlib.Path(path), file_format)
    if not prefix:
        return data or {}

    keys = [prefix] if isinstance(prefix, str) else prefix
    output = data
    for key in keys:
        output = output.get(key) or {}
    return output


def write(
    path: typing.Union[str, pathlib.Path],
    configs: typing.Dict[str, typing.Any],
    prefix: typing.Union[str, typing.Iterable[str]] = None,
    file_format: str = None,
) -> None:
    """
    Writes the specified configuration file with updated configuration data.
    If a prefix is specified, the data will be inserted at the given prefix.

    :param path:
        Path to the configuration file to read.
    :param configs:
        Updated lobotomy configuration data to be written to the file.
        This will replace the existing configuration data in the file.
    :param prefix:
        Optional prefix within the file in which the configuration resides.
    :param file_format:
        Optional format for the file, which will be determined from the
        file extension if omitted.
    :return:
        A dictionary containing the lobotomy configuration data from the
        given file. This will be an empty dictionary if no configuration
        exists yet.
    """
    keys = [prefix] if isinstance(prefix, str) else prefix
    path = pathlib.Path(path).expanduser().absolute()
    data = _read_file(path, file_format)

    child = data
    for key in keys or []:
        if key not in child:
            child[key] = {}
        child = child[key]

    child.update(configs)

    if file_format == "yaml" or path.name.endswith((".yaml", ".yml")):
        contents = yaml.safe_dump(data)
    elif file_format == "toml" or path.name.endswith(".toml"):
        contents = toml.dumps(data)
    else:
        contents = json.dumps(data, indent=2)

    path.write_text(contents)
