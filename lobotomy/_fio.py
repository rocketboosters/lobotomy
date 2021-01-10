import dataclasses
import json
import pathlib
import re
import textwrap
import typing

import toml
import yaml
import yaml.constructor

_indent_regex = re.compile(r"^(?P<indent>\s*)")
_path_regex = re.compile(r"!lobotomy.inject_(?P<kind>[^\s]+)\s+(?P<path>[^\s\n]+)")


@dataclasses.dataclass(frozen=True)
class YamlBlock:
    """Data structure for extracted YAML blocks"""

    #: Key within the larger context of the YAML data that this block data is
    #: associated with. The root YAML block should have an empty string for a key.
    key: str
    #: Line that precedes the body that contains the key.
    key_line: str
    #: The string contents of for the given key, not including the line with the
    #: key itself on it.
    body: str
    #: Absolute index where the block body starts in the YAML file that it was
    #: extracted from.
    start_index: int
    #: Absolute index where the block body ends (exclusive) in the YAML file
    #: that it was extracted from.
    end_index: int

    @property
    def key_index(self) -> int:
        """
        Index of the line where the key resides, which will be one less than the
        index where the body starts, unless the body starts at 0 because this is
        the root block.
        """
        return max(0, self.start_index - 1)

    @property
    def outer_body(self) -> str:
        """
        Body and the key line together instead of the body, which contains only
        the inner contents of the key.
        """
        if not self.key:
            return self.body

        return "{}\n{}".format(self.key_line, textwrap.indent(self.body, "  "))


def _get_block(key: str, block: YamlBlock) -> YamlBlock:
    """
    Retrieves the block within the specified argument block's body for the specified
    key. The body of a block has no key header line as the body is the string
    representation of the contents within the given block. Therefore, they search
    key, if present in the block, will be a top-level key in the block.

    :param key:
        Search key to extract from the specified block.
    :param block:
        Parent block in which to search for the specified key.
    :return:
        A new block containing the body contents of the specified key extracted from
        the contents of the parent block. If the key is not found a block will be
        returned with an empty body and start/end indexes of -1.
    """
    lines = block.body.split("\n")
    index_finder = (
        i for i, line in enumerate(lines) if line.strip().startswith(f"{key}:")
    )
    start = next(index_finder, None)
    if start is None:
        return YamlBlock(key, f"{key}:", "", -1, -1)

    output_lines = []
    for line in lines[(start + 1) :]:
        if not line.startswith(" "):
            break
        output_lines.append(line)

    offset = block.start_index + start + 1
    return YamlBlock(
        key,
        key_line=lines[start],
        body=textwrap.dedent("\n".join(output_lines)),
        start_index=offset,
        end_index=offset + len(output_lines),
    )


def _extract(
    contents: str,
    prefix: typing.Iterable[str],
) -> typing.Tuple[YamlBlock, YamlBlock, YamlBlock]:
    """
    Extracts the lobotomy sessions and clients blocks from the overall yaml block and
    returns them along with the lobotomy key-prefix yaml block in which the clients
    and sessions blocks were found.

    :param contents:
        YAML string contents from which to extract lobotomy data.
    :param prefix:
        Key prefix within the YAML string where the lobotomy data resides.
    :return:
        Clients block, sessions block, and parent lobotomy block.
    """
    body = textwrap.dedent(contents.strip().replace("\r", ""))
    prefix_block = YamlBlock("", "", body, 0, 1 + body.count("\n"))
    for key in prefix:
        prefix_block = _get_block(key, prefix_block)

    return (
        _get_block("clients", prefix_block),
        _get_block("sessions", prefix_block),
        prefix_block,
    )


def _get_prefix(
    prefix: typing.Union[None, str, typing.Iterable[str]],
) -> typing.Iterable[str]:
    """
    Optional prefix that specifies where within the data dictionary to find the
    lobotomized data. If not specified, the data dictionary is assumed to be a
    lobotomy data configuration dictionary. If specified, the prefix can either
    be represented as a hierarchical list of keys to descend within the root
    data dictionary, e.g. ["foo", "bar"] or as a dot-delimited string denoting
    the hierarchical list of keys, e.g. "foo.bar". If one of the keys contains
    a "." then the list form must be used.
    """
    if not prefix:
        return []

    return prefix.split(".") if isinstance(prefix, str) else prefix


def _normalize_yaml(contents: str, directory: pathlib.Path) -> str:
    """
    Normalizes Yaml class configuration for advanced loading functionality.

    :param contents:
        String contents of a YAML file to be parsed.
    :param directory:
        Absolute directory to the folder location for the loaded YAML file.
    """

    def path_replacer(match: re.Match) -> str:

        kind = match.group("kind")
        source = match.group("path").strip("\"'")
        p = directory.joinpath(source).expanduser().absolute()
        value = json.dumps({"absolute": str(p), "original": source})
        return f"!lobotomy.inject_{kind} '{value}'"

    normalized = re.sub(_path_regex, path_replacer, contents)
    return normalized


def _read_yaml(
    contents: str,
    prefix: typing.Iterable[str],
    directory: pathlib.Path,
) -> dict:
    """
    Reads a YAML file into lobotomy data. First it tries to read the entire file,
    but if that does not work it falls back to extracting the lobotomy data from
    the file and then loading only that portion of the file. This is useful when
    YAML classes are used within the file that may not be loaded at the time of
    the file read process.

    :param contents:
        YAML string contents from which to extract lobotomy data.
    :param prefix:
        Key prefix within the YAML string where the lobotomy data resides.
    :param directory:
        Directory to the folder in which the YAML file resides.
    :return:
        Lobotomy data loaded from the YAML string by either of the methods.
    """
    normalized = _normalize_yaml(contents, directory)
    try:
        output = yaml.full_load(normalized)
        for key in prefix:
            output = output.get(key) or {}
        return {k: v for k, v in output.items() if k in ("clients", "sessions")}
    except yaml.constructor.ConstructorError:
        pass

    clients_block, sessions_block, _ = _extract(normalized, prefix)
    data = {}
    if clients_block.start_index != -1:
        data.update(yaml.full_load(clients_block.outer_body))
    if sessions_block.start_index != -1:
        data.update(yaml.full_load(sessions_block.outer_body))
    return data


def _read_file_data(
    path: pathlib.Path,
    file_format: typing.Optional[str],
) -> dict:
    """..."""
    contents = path.read_text()

    if file_format == "yaml" or path.name.endswith((".yaml", ".yml")):
        return yaml.full_load(_normalize_yaml(contents, path.parent))

    if file_format == "toml" or path.name.endswith(".toml"):
        return typing.cast(dict, toml.loads(contents))

    return json.loads(contents)


def _read_file(
    path: pathlib.Path,
    file_format: typing.Optional[str],
    prefix: typing.Iterable[str],
) -> dict:
    """
    Reads the configuration file from disk if it exists.

    :param path:
        Location of the file to read.
    :param file_format:
        Specifies the format of the file to load. If None the extension of the
        file path will be used to determine the type of file to read.
    :param prefix:
        Key prefix within the YAML string where the lobotomy data resides.
    :return:
        Lobotomy data loaded from the file at the specified prefix.
    """
    p = path.expanduser().absolute()
    if not p.exists():
        raise FileNotFoundError(f"Missing file {p}")

    try:
        output = _read_file_data(p, file_format) or {}
    except yaml.constructor.ConstructorError:
        return _read_yaml(p.read_text(), prefix, p.parent)

    for key in prefix:
        output = output.get(key) or {}
    return {k: v for k, v in output.items() if k in ("clients", "sessions")}


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
    return _read_file(pathlib.Path(path), file_format, _get_prefix(prefix))


def _update_yaml_write_lines(
    lines: typing.List[str],
    configs: typing.Dict[str, typing.Any],
    block: YamlBlock,
    parent: YamlBlock,
) -> typing.List[str]:
    """
    Replaces the specified block within the YAML file lines object with the new
    configs body by dumping that body and replacing it within the returned list
    of lines.

    :param lines:
        Complete YAML file lines for the file that will be written. A modified
        version of these will be returned that remove the existing lines for
        the target block and replace them with the new data stored in the lobotomy
        data configs object. If the new configuration is empty for the block, the
        existing lines will be extracted and no new lines added to the returned
        lines list.
    :param configs:
        Lobotomy data from which the new block configuration will be generated.
    :param block:
        YamlBlock to be updated in the output with the new configs data.
    :param parent:
        Parent YamlBlock in which the specified block resides, which is used to
        handle cases where the block definition is new.
    :return:
        A modified version of the lines argument where the old block data has
        been removed and replaced by the new block data serialized from the
        specified lobotomy data configs.
    """
    if parent.key == "":
        # If there is no key for the parent, it's the root of the file and there
        # will be no indent.
        indent = ""
    else:
        index = parent.key_index if block.start_index == -1 else block.key_index
        indent = _indent_regex.match(lines[index]).group("indent")  # type: ignore

    if data := configs.get(block.key):
        new_body = [textwrap.indent(yaml.dump({block.key: data}), indent).rstrip()]
    else:
        # Don't include the body if the configuration is empty.
        new_body = []

    if block.start_index == -1:
        before = lines[: (parent.key_index + 1)]
        after = lines[(parent.key_index + 1) :]
    else:
        before = lines[: block.key_index]
        after = lines[block.end_index :]
    return before + new_body + after


def _write_modified_yaml(
    path: pathlib.Path,
    configs: typing.Dict[str, typing.Any],
    prefix: typing.Iterable[str],
) -> None:
    """
    Writes the updated lobotomy data configs to an existing YAML file without loading
    the entire file to prevent issues with YAML classes.

    :param path:
        Path where the lobotomy data will be written.
    :param configs:
        Lobotomy data to write to the file.
    :param prefix:
        Key hierarchy where the lobotomy data will be written within the file.
    """
    body = textwrap.dedent(path.read_text().strip().replace("\r", ""))
    lines = body.split("\n")
    clients_block, sessions_block, parent_block = _extract(body, prefix)

    # Sort the blocks so that they are modified from bottom of the file to
    # the top so that line index changes don't corrupt earlier block index
    # values.
    blocks = sorted(
        [clients_block, sessions_block],
        key=lambda b: b.start_index,
        reverse=True,
    )
    for block in blocks:
        lines = _update_yaml_write_lines(lines, configs, block, parent_block)

    body = "{}\n".format("\n".join(lines))
    path.write_text(body)


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
    prefix_keys = _get_prefix(prefix)
    p = pathlib.Path(path).expanduser().absolute()

    # Make sure the configs are clean of everything but the expected lobotomy keys.
    source = {k: v for k, v in configs.items() if k in ("clients", "sessions")}

    is_yaml = file_format == "yaml" or p.name.endswith((".yml", ".yaml"))
    if p.exists() and is_yaml:
        _write_modified_yaml(p, source, prefix_keys)
        return

    if p.exists():
        data = _read_file_data(p, file_format)
    else:
        data = {}

    child = data
    for key in prefix_keys or []:
        if key not in child:
            child[key] = {}
        child = child[key]

    child.update(source)

    if file_format == "yaml" or p.name.endswith((".yml", ".yaml")):
        contents = yaml.dump(data)
    elif file_format == "toml" or p.name.endswith(".toml"):
        contents = toml.dumps(data)
    else:
        contents = json.dumps(data, indent=2)

    p.write_text(contents)
