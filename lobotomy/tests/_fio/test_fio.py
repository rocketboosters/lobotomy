import difflib
import pathlib
import typing
from unittest.mock import MagicMock
from unittest.mock import patch

import yaml
from pytest import mark

import lobotomy
from lobotomy import _fio

_directory = pathlib.Path(__file__).parent.joinpath("scenarios").absolute()
_folders = [item.name for item in _directory.iterdir() if item.is_dir()]


def _get_path(directory: pathlib.Path, base_name: str) -> pathlib.Path:
    """Finds the existing path with one of the allowed extensions."""
    options = ("yaml", "json", "toml", "txt")
    return next(
        d for ext in options if (d := directory.joinpath(f"{base_name}.{ext}")).exists()
    )


def _process_action(
    lobotomized: lobotomy.Lobotomy,
    action: typing.Dict[str, typing.Any],
) -> None:
    """Mutates the lobotomized data according the specified action."""
    kind = action.get("kind")
    data = lobotomized.data
    clients = data.get("clients", {})

    if kind == "remove_service_calls":
        service = action["service"]
        method = action["method"]
        del clients[service][method]
    elif kind == "remove_service":
        service = action["service"]
        del clients[service]
    elif kind == "add_service_call":
        lobotomized.add_call(
            service_name=action["service"],
            method_name=action["method"],
            response=action.get("response"),
        )


@mark.parametrize("folder", _folders)
@patch("lobotomy._fio.pathlib.Path.write_text")
def test_fio(write_text: MagicMock, folder: str):
    """
    Should carry out the scenario, reading the scenario file without error and
    then writing the results to the mocked output such that they equal the expected
    text for the given scenario.
    """
    d = _directory.joinpath(folder)
    settings = yaml.full_load(d.joinpath("settings.yaml").read_text())

    prefix = settings.get("lobotomy_prefix")
    scenario_path = _get_path(d, "scenario")

    with lobotomy.Patch(path=scenario_path, prefix=prefix) as lobotomized:
        for action in settings.get("actions", []):
            _process_action(lobotomized, action)
        _fio.write(scenario_path, lobotomized.data, prefix=prefix)

    # Load expected and remove comments.
    lines = _get_path(d, "expected").read_text().strip().replace("\r", "").split("\n")
    expected = "\n".join([line for line in lines if not line.lstrip().startswith("#")])

    observed: str = write_text.call_args.args[0].strip().replace("\r", "")
    difference = "\n".join(
        difflib.unified_diff(
            expected.split("\n"),
            observed.split("\n"),
            fromfile="expected",
            tofile="observed",
        )
    )
    assert (
        not difference
    ), f"\nEXPECTED:\n{expected}\nOBSERVED:\n{observed}\nDIFFERENCE:\n{difference}"
