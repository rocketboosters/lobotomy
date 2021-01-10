import dataclasses
import importlib.resources
import json
import pathlib
import typing

import botocore
import yaml

from lobotomy._services import _formating


@dataclasses.dataclass(frozen=True)
class DataWrapper:
    """
    Data structure class containing a data object and a get method
    that allows for hierarchical, optional-chaining lookup of keys
    within the data object.
    """

    data: dict

    def get(self, *args: str, default: typing.Any = None) -> typing.Any:
        """
        Fetches the value from the spec dictionary, allowing for nested
        key lookups by specifying multiple key args. If the key is not
        found in the spec dictionary, the default value will be returned
        instead. However, if a falsy value is found for the key, including
        None, that will be returned instead.
        """
        value = self.data or {}
        for k in args:
            if k not in value:
                return default
            value = value[k]
        return value


@dataclasses.dataclass(frozen=True)
class Method(DataWrapper):
    """Client method definition data structure."""

    #: Method name for the service client represented by this object.
    name: str
    #: Method operation definition from the service specification.
    data: dict
    #: Service in which this method resides.
    service: "Service"

    @property
    def input(self) -> dict:
        """Definition for the input signature of this method."""
        return _formating.parse_definition_item(
            self.service.shapes,
            self.get("input") or {},
        )

    @property
    def output(self) -> dict:
        """Definition for the output/response signature of this method."""
        return _formating.parse_definition_item(
            self.service.shapes,
            self.get("output") or {},
        )

    @property
    def configuration_output(self) -> typing.Any:
        """
        A configuration representation of the method output for
        use in lobotomy service method configurations.
        """
        return _formating.flat_cast(self.output)


@dataclasses.dataclass(frozen=True)
class Service(DataWrapper):
    """
    Botocore service definition for the specified service with accessors
    and added functionality for use in lobotomy mocking situations.
    """

    #: Name of the service for the associated specification.
    name: str
    #: Dictionary containing the loaded botocore specification for the
    #: given service name.
    data: dict = dataclasses.field(init=False, default_factory=lambda: {})
    #: The exceptions for the associated service.
    exceptions: dict = dataclasses.field(init=False, default_factory=lambda: {})

    def __post_init__(self):
        """Loads the service specification into the object."""
        self.data.update(_get_specification(self.name))
        self.exceptions.update(_get_exceptions(self.data))

    @property
    def version(self) -> str:
        """Version of the service specification."""
        return self.get("version", "1.0")

    @property
    def metadata(self) -> dict:
        """
        Metadata associated with the service as defined in the botocore
        specification.
        """
        return self.get("metadata") or {}

    @property
    def operations(self) -> dict:
        """
        A dictionary that maps client methods to their specifications.
        The method keys are all lowercase format, so it's best to use
        the Service.lookup(method_name) to retrieve the values for
        snake_case definitions.
        """
        return self.get("operations") or {}

    @property
    def shapes(self) -> dict:
        """
        Shape definitions from the service specification that define the
        input, output and exception type objects and their arguments.
        """
        return self.get("shapes") or {}

    def has(self, method_name: str) -> bool:
        """Determines whether or not the spec defines the given method."""
        value = method_name.lower().replace("_", "")
        return value in self.operations

    def lookup(self, method_name: str) -> "Method":
        """Fetch the Method data for the associated method name."""
        value = method_name.lower().replace("_", "")
        return Method(
            name=method_name,
            data=self.operations.get(value) or {},
            service=self,
        )


def _get_specification(service_name: str) -> dict:
    """
    Loads the service specification data for the given service name from
    the installed botocore library.

    :param service_name:
        Name of the service to load, which corresponds with the name that
        would be given to create the service client object.
    :return:
        Dictionary containing the loaded JSON service specification for the
        botocore service. The operations section is modified such that the
        keys (i.e. method names) are all lowercase because the service spec
        defines them as PascalCase and that is difficult to lookup when the
        snake_case names are the ones invoked on the client.
    """
    directory = (
        pathlib.Path(botocore.__file__).parent.joinpath("data", service_name).absolute()
    )
    folder = next(
        (
            n
            for n in sorted(directory.iterdir(), reverse=True)
            if n.name.startswith("20")
        )
    )
    spec = json.loads(
        directory.joinpath(folder, "service-2.json").read_text(encoding="utf-8")
    )

    # Augment the botocore service definitions with client additions added by boto3
    # for non-standard api operations. The notable example here is s3.upload_file,
    # which is a convenience wrapper around the much lower-level multipart upload
    # api methods.
    package = f"{__package__}._augmentations"
    resource_name = f"{service_name}.yaml"
    if importlib.resources.is_resource(package, resource_name):
        extras = yaml.full_load(importlib.resources.read_text(package, resource_name))

        for key, value in (extras.get("operations") or {}).items():
            spec["operations"][key] = value

        for key, value in (extras.get("shapes") or {}).items():
            spec["shapes"][key] = value

    spec["operations"] = {k.lower(): v for k, v in spec["operations"].items()}
    return spec


def _get_exceptions(specification: dict) -> typing.Dict[str, dict]:
    """
    Assembles a mapping of client exceptions raised by the methods in
    the specified service specification where the values are the shape
    mappings for those exceptions as specified in the service specification.

    :param specification:
        Botocore service specification from which to extract exception
        information.
    :return:
        Dictionary of exception names and their corresponding shapes
        set on the client.exceptions object.
    """
    errors = {
        error["shape"]
        for item in specification["operations"].values()
        for error in (item.get("errors") or [])
    }
    return {e: specification["shapes"][e] for e in errors}
