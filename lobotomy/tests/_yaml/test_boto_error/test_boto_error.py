import pathlib

import pytest

import lobotomy

directory = pathlib.Path(__file__).parent.absolute()


@lobotomy.patch(path=directory.joinpath("scenario.yaml"))
def test_boto_error(lobotomized: lobotomy.Lobotomy):
    """Should create an error response."""
    client = lobotomized().client("lambda")

    with pytest.raises(client.exceptions.ResourceNotFoundException):
        client.get_function_configuration(FunctionName="foo")
