import datetime
import typing

import boto3
from pytest import mark

import lobotomy

values = [
    "2020-01-01",
    "2020-01-01T12:23:34",
    "2020-01-01T12:23:34Z",
    "2020-01-01T12:23:34+00:00",
    datetime.date(2020, 1, 1),
    datetime.datetime(2020, 1, 1, 12, 23, 34, tzinfo=None),
    datetime.datetime(2020, 1, 1, 12, 23, 34, tzinfo=datetime.timezone.utc),
]


@mark.parametrize("value", values)
@lobotomy.Patch()
def test_timestamp_formats(lobotomized: lobotomy.Lobotomy, value: typing.Any):
    """Should cast timestamp values correctly."""
    lobotomized.add_call("iam", "get_role", response={"Role": {"CreateDate": value}})
    response = boto3.Session().client("iam").get_role(RoleName="foo")
    observed: datetime.datetime = response["Role"]["CreateDate"]
    assert isinstance(observed, datetime.datetime)
    assert observed.date() == datetime.date(2020, 1, 1)
    assert observed.hour in (0, 12)
    assert observed.minute in (0, 23)
    assert observed.second in (0, 34)
