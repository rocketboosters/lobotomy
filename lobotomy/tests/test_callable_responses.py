import typing

import lobotomy


def _respond(*args, **kwargs) -> typing.Dict[str, typing.Any]:
    return {"Body": "{}.{}".format(kwargs["Bucket"], kwargs["Key"]).encode()}


@lobotomy.patch()
def test_callable_responses(lobotomized: "lobotomy.Lobotomy"):
    """Should return the expected body value from the callable response."""
    lobotomized.add_call("s3", "get_object", _respond)
    session = lobotomized()
    client = session.client("s3")

    response = client.get_object(Bucket="foo", Key="bar")
    assert response["Body"].read() == b"foo.bar"
