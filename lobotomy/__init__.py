import pathlib as _pathlib
from importlib import metadata as _metadata

import toml as _toml

from ._cli import run as run_cli  # noqa: F401
from ._clients import Client  # noqa: F401
from ._exceptions import ClientError  # noqa: F401
from ._exceptions import DataTypeError  # noqa: F401
from ._exceptions import NoResponseFound  # noqa: F401
from ._exceptions import NoSuchMethod  # noqa: F401
from ._exceptions import RequestValidationError  # noqa: F401
from ._mocking import Patch  # noqa: F401
from ._mocking import patch  # noqa: F401
from ._sessions import Lobotomy  # noqa: F401
from ._sessions import ServiceCall  # noqa: F401
from ._sessions import Session  # noqa: F401
from ._yaml import InjectString  # noqa: F401
from ._yaml import ToJson  # noqa: F401
from ._yaml import YamlModifier  # noqa: F401

try:
    __version__ = _metadata.version(__package__)
except _metadata.PackageNotFoundError:  # pragma: no cover
    # If the package is not installed such that it has distribution metadata
    # fallback to loading the version from the pyproject.toml file.
    __version__ = _toml.loads(
        _pathlib.Path(__file__).parent.parent.joinpath("pyproject.toml").read_text()
    )["tool"]["poetry"]["version"]
