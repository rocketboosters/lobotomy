import json
from unittest.mock import MagicMock
from unittest.mock import patch

import toml
import yaml
from pytest import mark

from lobotomy import _fio

SOURCE_DATA: dict = {
    "prefix": {
        "subprefix": {
            "clients": {
                "sts": {"get_caller_identity": {}},
            }
        }
    }
}

SCENARIOS = (
    {"file_format": "json", "data": json.dumps(SOURCE_DATA)},
    {"file_format": "yaml", "data": yaml.safe_dump(SOURCE_DATA)},
    {"file_format": "toml", "data": toml.dumps(SOURCE_DATA)},
)


def _make_path(
    data: str,
    file_format: str = "json",
    exists: bool = True,
):
    """Creates a mocked pathlib.Path object to return and use during testing."""
    path = MagicMock()
    path.name = f"foo.{file_format}"
    path.exists.return_value = exists
    path.read_text.return_value = data
    path.expanduser.return_value = path
    path.absolute.return_value = path
    return path


@mark.parametrize("scenario", SCENARIOS)
@patch("lobotomy._fio.pathlib.Path")
def test_read(pathlib_path: MagicMock, scenario: dict):
    """Should successfully read the file."""
    path = _make_path(**scenario)
    pathlib_path.return_value = path
    result = _fio.read(path, ["prefix", "subprefix"])
    assert result == SOURCE_DATA["prefix"]["subprefix"]


@mark.parametrize("scenario", SCENARIOS)
@patch("lobotomy._fio.pathlib.Path")
def test_read_new_prefix(pathlib_path: MagicMock, scenario: dict):
    """Should successfully read the file even non-existent prefix."""
    path = _make_path(**scenario)
    pathlib_path.return_value = path
    result = _fio.read(path, ["foo", "bar"])
    assert result == {}


@patch("lobotomy._fio.pathlib.Path")
def test_read_no_prefix(pathlib_path: MagicMock):
    """Should successfully read the file with no key prefix."""
    path = _make_path("{}", "json")
    pathlib_path.return_value = path
    assert _fio.read(path) == {}


@patch("lobotomy._fio.pathlib.Path")
def test_read_not_exists(pathlib_path: MagicMock):
    """Should return None if file does not exist."""
    path = _make_path("{}", exists=False)
    pathlib_path.return_value = path
    assert _fio.read(path, ["prefix", "subprefix"]) == {}


@mark.parametrize("scenario", SCENARIOS)
@patch("lobotomy._fio.pathlib.Path")
def test_write(pathlib_path: MagicMock, scenario: dict):
    """Should successfully write changes to the file."""
    path = _make_path(**scenario)
    pathlib_path.return_value = path
    _fio.write(path, {"clients": {}}, ["prefix", "subprefix"])
    assert path.write_text.call_args.args[0].find("get_caller_identity") == -1


@mark.parametrize("scenario", SCENARIOS)
@patch("lobotomy._fio.pathlib.Path")
def test_write_new_prefix(pathlib_path: MagicMock, scenario: dict):
    """Should successfully write changes to the file at a new prefix."""
    path = _make_path(**scenario)
    pathlib_path.return_value = path
    _fio.write(path, {"hello": "bar"}, ["foo", "bar"])
    assert path.write_text.call_args.args[0].find("get_caller_identity") > 0
    assert path.write_text.call_args.args[0].find("hello") > 0
