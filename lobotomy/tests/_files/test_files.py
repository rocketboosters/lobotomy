import pathlib

import boto3
import pytest
from pytest import mark

import lobotomy as lbm

DIRECTORY = pathlib.Path(__file__).parent.absolute()

SCENARIOS = (
    {"file": "example.yaml"},
    {"file": "example.toml"},
    {"file": "example.json"},
)


@mark.parametrize("scenario", SCENARIOS)
def test_files(scenario: dict):
    """Should execute the scenario as expected"""
    path = DIRECTORY.joinpath(scenario["file"])
    lobotomy = lbm.Lobotomy.from_file(path)
    session = lobotomy()

    client = session.client("sts")
    assert client.get_caller_identity()["Account"] == "123"

    client = session.client("lambda")
    assert client.get_function_configuration(FunctionName="foo") == {}

    with pytest.raises(lbm.ClientError) as exception_info:
        client.get_function_configuration(FunctionName="foo")

    assert exception_info.value.response["Error"]["Code"]


@lbm.Patch(path=DIRECTORY.joinpath("example.yaml"))
def test_files_patched(lobotomy: lbm.Lobotomy):
    """Should execute the scenario as expected"""
    session = boto3.Session()

    client = session.client("sts")
    assert client.get_caller_identity()["Account"] == "123"

    client = session.client("lambda")
    assert client.get_function_configuration(FunctionName="foo") == {}

    with pytest.raises(lbm.ClientError) as exception_info:
        client.get_function_configuration(FunctionName="foo")

    assert exception_info.value.response["Error"]["Code"]
