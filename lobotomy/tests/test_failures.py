import pathlib

import boto3
import pytest

import lobotomy


def test_missing_file_patch():
    """Should raise a patch error when neither data nor path are specified."""
    fake_path = pathlib.Path(__file__).parent.joinpath("fake.yaml")
    with pytest.raises(FileNotFoundError):
        lobotomy.Patch(path=fake_path)(lambda *args, **kwargs: 1)()


@lobotomy.Patch(data={"clients": {"lambda": {}}})
def test_no_such_method(*args):
    """Should raise error when calling a non-existent client method."""
    session = boto3.Session()
    with pytest.raises(lobotomy.NoSuchMethod):
        session.client("lambda").foo()


@lobotomy.Patch(data={"clients": {"s3": {}}})
def test_no_data_specified(*args):
    """Should raise error when no response has been supplied."""
    session = boto3.Session()
    with pytest.raises(lobotomy.NoResponseFound):
        session.client("s3").put_object()


@lobotomy.Patch()
def test_missing_request_arguments(lobotomized: lobotomy.Lobotomy):
    """Should fail due to missing "Bucket" request argument."""
    lobotomized.add_call("s3", "list_objects", {})
    session = boto3.Session()
    client = session.client("s3")
    with pytest.raises(lobotomy.RequestValidationError):
        client.list_objects()


@lobotomy.Patch()
def test_unknown_request_arguments(lobotomized: lobotomy.Lobotomy):
    """Should fail due to presence of unknown "Foo" argument."""
    lobotomized.add_call("s3", "list_objects", {})
    session = boto3.Session()
    client = session.client("s3")
    with pytest.raises(lobotomy.RequestValidationError):
        client.list_objects(Bucket="foo", Foo="bar")


@lobotomy.Patch()
def test_bad_casting(lobotomized: lobotomy.Lobotomy):
    """Should fail to cast dictionary as string."""
    lobotomized.add_call("s3", "list_objects", {"Contents": ["should-be-dict"]})
    session = boto3.Session()
    client = session.client("s3")
    with pytest.raises(lobotomy.DataTypeError):
        client.list_objects(Bucket="foo")


@lobotomy.Patch()
def test_client_errors(lobotomized: lobotomy.Lobotomy):
    """Should raise the specified error."""
    lobotomized.add_call(
        service_name="s3",
        method_name="list_objects",
        response={"Error": {"Code": "NoSuchBucket", "Message": "Hello..."}},
    )
    session = boto3.Session()
    client = session.client("s3")
    with pytest.raises(client.exceptions.NoSuchBucket):
        client.list_objects(Bucket="foo")

    with pytest.raises(lobotomy.ClientError) as exception_info:
        client.list_objects(Bucket="foo")

    assert exception_info.value.response["Error"]["Code"] == "NoSuchBucket"
