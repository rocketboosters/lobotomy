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
        """Convert the modifier to its response format."""
        return None

    @classmethod
    def label(cls) -> str:
        """Get the yaml identifier representation for the class."""
        return "!lobotomy.unknown"

    @classmethod
    def _from_yaml(cls, loader: yaml.Loader, node: yaml.Node) -> "YamlModifier":
        """Load an internal yaml node parsing, defaulting to a scalar value."""
        value = loader.construct_scalar(typing.cast(yaml.ScalarNode, node))
        return cls(value)

    @classmethod
    def parse_yaml(cls, loader: yaml.Loader, node: yaml.Node) -> "YamlModifier":
        """Parse yaml node into this class object for Lobotomy processing."""
        return cls._from_yaml(loader, node)

    @classmethod
    def _dump_yaml(cls, dumper: yaml.Dumper, source: "YamlModifier") -> typing.Any:
        """Convert to a yaml node representation for writing to file."""
        return dumper.represent_scalar(source.label(), source.value)

    @classmethod
    def dump_yaml(cls, dumper: yaml.Dumper, source: "YamlModifier") -> typing.Any:
        """Dump to a yaml node representation for writing to file."""
        return cls._dump_yaml(dumper, source)

    @classmethod
    def register(cls):
        """Register the comparator with the PyYaml loader."""
        yaml.add_constructor(cls.label(), cls.parse_yaml)
        yaml.add_representer(cls, cls.dump_yaml)


@dataclasses.dataclass()
class ToJson(YamlModifier):
    """YAML class for converting a YAML object into a JSON string in a response."""

    def to_response_data(self) -> typing.Any:
        """Convert the modifier to its response format."""
        return json.dumps(self.value)

    @classmethod
    def label(cls) -> str:
        """Get the yaml identifier representation for the class."""
        return "!lobotomy.to_json"

    @classmethod
    def _from_yaml(cls, loader: yaml.Loader, node: yaml.Node) -> "ToJson":
        """Load an internal yaml node parsing."""
        value = loader.construct_mapping(node, deep=True)
        return cls(value)

    @classmethod
    def _dump_yaml(cls, dumper: yaml.Dumper, source: "YamlModifier") -> typing.Any:
        """Convert to a yaml node representation for writing to file."""
        return dumper.represent_mapping(source.label(), source.value)


@dataclasses.dataclass()
class InjectString(YamlModifier):
    """YAML class for including an external file as a string value."""

    def to_response_data(self) -> typing.Any:
        """Convert the modifier to its response format."""
        return pathlib.Path(self.value["absolute"]).expanduser().absolute().read_text()

    @classmethod
    def label(cls) -> str:
        """Get the yaml identifier representation for the class."""
        return "!lobotomy.inject_string"

    @classmethod
    def _from_yaml(cls, loader: yaml.Loader, node: yaml.Node) -> "InjectString":
        """Load an internal yaml node parsing."""
        raw = loader.construct_scalar(typing.cast(yaml.ScalarNode, node))
        value = json.loads(typing.cast(str, raw).strip("\"'"))
        return cls(value)

    @classmethod
    def _dump_yaml(cls, dumper: yaml.Dumper, source: "YamlModifier") -> typing.Any:
        """Convert to a yaml node representation for writing to file."""
        return dumper.represent_scalar(source.label(), source.value["original"])


@dataclasses.dataclass()
class BotoError(YamlModifier):
    """YAML class for specifying boto errors for service calls."""

    def to_response_data(self) -> typing.Any:
        """Convert the modifier to its response format."""
        v = self.value or {}
        error_code = v.get("code", "GenericLobotomyError")
        error_message = v.get("message", "There was an error.")
        return {"Error": {"Code": error_code, "Message": error_message}}

    @classmethod
    def label(cls) -> str:
        """Get the yaml identifier representation for the class."""
        return "!lobotomy.error"

    @classmethod
    def _from_yaml(cls, loader: yaml.Loader, node: yaml.Node) -> "BotoError":
        """Load an internal yaml node parsing."""
        value = loader.construct_mapping(node, deep=True)
        return cls(value)

    @classmethod
    def _dump_yaml(cls, dumper: yaml.Dumper, source: "YamlModifier") -> typing.Any:
        """Convert to a yaml node representation for writing to file."""
        return dumper.represent_mapping(source.label(), source.value or {})


ToJson.register()
InjectString.register()
BotoError.register()
