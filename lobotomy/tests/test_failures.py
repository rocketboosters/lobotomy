import pathlib

import boto3
import pytest

import lobotomy as lbm


def test_bad_patch():
    """Should raise a patch error when neither data nor path are specified."""
    with pytest.raises(ValueError):
        lbm.Patch()(lambda *args, **kwargs: 1)


def test_missing_file_patch():
    """Should raise a patch error when neither data nor path are specified."""
    fake_path = pathlib.Path(__file__).parent.joinpath("fake.yaml")
    with pytest.raises(FileNotFoundError):
        lbm.Patch(path=fake_path)(lambda *args, **kwargs: 1)


@lbm.Patch(data={"clients": {"lambda": {}}})
def test_no_such_method(*args):
    """Should raise error when calling a non-existent client method."""
    session = boto3.Session()
    with pytest.raises(ValueError):
        session.client("lambda").foo()


@lbm.Patch(data={"clients": {"s3": {}}})
def test_no_data_specified(*args):
    """Should raise error when no response has been supplied."""
    session = boto3.Session()
    with pytest.raises(ValueError):
        session.client("s3").put_object()
