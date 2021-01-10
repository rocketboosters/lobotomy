import dataclasses
import json
import pathlib
import typing

import yaml


@dataclasses.dataclass()
class YamlModifier:
    """Base class for lobotomy YAML modifier class."""

    value: typing.Any

    def to_response_data(self) -> typing.Any:
        """Converts the modifier to its response format."""
        return None

    @classmethod
    def label(cls) -> str:
        return "!lobotomy.unknown"

    @classmethod
    def _from_yaml(cls, loader: yaml.Loader, node: yaml.Node) -> "YamlModifier":
        """Internal yaml node parsing. Defaults to a scalar value."""
        value = loader.construct_scalar(node)
        return cls(value)

    @classmethod
    def parse_yaml(cls, loader: yaml.Loader, node: yaml.Node) -> "YamlModifier":
        """Yaml alternative constructor that builds the comparator from a yaml node."""
        return cls._from_yaml(loader, node)

    @classmethod
    def _dump_yaml(cls, dumper: yaml.Dumper, source: "YamlModifier") -> typing.Any:
        return dumper.represent_scalar(source.label(), source.value)

    @classmethod
    def dump_yaml(cls, dumper: yaml.Dumper, source: "YamlModifier") -> typing.Any:
        return cls._dump_yaml(dumper, source)

    @classmethod
    def register(cls):
        """Registers the comparator with the PyYaml loader."""
        yaml.add_constructor(cls.label(), cls.parse_yaml)
        yaml.add_representer(cls, cls.dump_yaml)


@dataclasses.dataclass()
class ToJson(YamlModifier):
    """YAML class for converting a YAML object into a JSON string in a response."""

    def to_response_data(self) -> typing.Any:
        return json.dumps(self.value)

    @classmethod
    def label(cls) -> str:
        return "!lobotomy.to_json"

    @classmethod
    def _from_yaml(cls, loader: yaml.Loader, node: yaml.Node) -> "ToJson":
        """Internal yaml node parsing. Defaults to a scalar value."""
        value = loader.construct_mapping(node, deep=True)
        return cls(value)

    @classmethod
    def _dump_yaml(cls, dumper: yaml.Dumper, source: "YamlModifier") -> typing.Any:
        return dumper.represent_mapping(source.label(), source.value)


@dataclasses.dataclass()
class InjectString(YamlModifier):
    """YAML class for including an external file as a string value."""

    def to_response_data(self) -> typing.Any:
        return pathlib.Path(self.value["absolute"]).expanduser().absolute().read_text()

    @classmethod
    def label(cls) -> str:
        return "!lobotomy.inject_string"

    @classmethod
    def _from_yaml(cls, loader: yaml.Loader, node: yaml.Node) -> "InjectString":
        """Internal yaml node parsing. Defaults to a scalar value."""
        value = json.loads(loader.construct_scalar(node).strip("\"'"))
        return cls(value)

    @classmethod
    def _dump_yaml(cls, dumper: yaml.Dumper, source: "YamlModifier") -> typing.Any:
        return dumper.represent_scalar(source.label(), source.value["original"])


ToJson.register()
InjectString.register()
