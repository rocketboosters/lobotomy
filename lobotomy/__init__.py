import pathlib as _pathlib
from importlib import metadata as _metadata

import toml as _toml

from ._cli import run as run_cli  # noqa
from ._clients import Client  # noqa
from ._clients import ClientError  # noqa
from ._mocking import Patch  # noqa
from ._sessions import Lobotomy  # noqa
from ._sessions import Session  # noqa

try:
    __version__ = _metadata.version(__package__)
except _metadata.PackageNotFoundError:  # pragma: no-cover
    # If the package is not installed such that it has distribution metadata
    # fallback to loading the version from the pyproject.toml file.
    __version__ = _toml.loads(
        _pathlib.Path(__file__).parent.parent.joinpath("pyproject.toml").read_text()
    )["tool"]["poetry"]["version"]
