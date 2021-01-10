import datetime
import typing
from unittest.mock import MagicMock

import dateutil.parser
from botocore.response import StreamingBody

import lobotomy


class InternalStreamer:
    """
    An internal class that replaces the HTTPResponse object that boto
    StreamingBody objects wrap. This is used to simulate the streaming
    body behaviors in returned streaming response objects.
    """

    def __init__(self, source: typing.Union[bytes, str]):
        """Wrap the source string in a streaming interface."""
        self._cursor = 0
        self._source: typing.Union[bytes, str] = source

        # This exists for botocore compatibility setting timeouts.
        self._fp = MagicMock()

    def read(self, amt: int = None):
        """Simulates the streaming interface."""
        length = len(self._source)
        amount = amt if amt is not None else length
        start = max(0, self._cursor)
        end = min(length, self._cursor + amount)
        self._cursor = end
        return self._source[start:end]

    def close(self):
        # Exists only for compatibility cases.
        pass

    def __len__(self):
        return len(self._source)


def _cast_structure(definition: dict, value: dict) -> dict:
    """
    Converts a dictionary/structure botocore type into its formatted values
    by recursively casting all the members.

    :param definition:
        Specification definition for the associated value to cast.
    :param value:
        A loaded value to be cast into its boto client response value.
    :return:
        The cast version of the specified value that matches the format of
        the value as it would be returned in a boto client response.
    """
    return {k: cast(definition["members"].get(k), v) for k, v in value.items()}


def _cast_noop(definition: dict, value: typing.Any) -> typing.Any:
    """
    A non-casting, no-op operation used for unknown or uncastable value
    types.

    :param definition:
        Specification definition for the associated value to cast.
    :param value:
        A loaded value to be cast into its boto client response value.
    :return:
        An unmodified value as this is a no-op.
    """
    return value


def _cast_integer(definition: dict, value: typing.Any) -> int:
    """
    Converts a value into an integer value.

    :param definition:
        Specification definition for the associated value to cast.
    :param value:
        A loaded value to be cast into its boto client response value.
    :return:
        The cast version of the specified value that matches the format of
        the value as it would be returned in a boto client response.
    """
    return int(value)


def _cast_list(definition: dict, value: list) -> list:
    """
    Converts a list botocore type into its formatted values
    by recursively casting all the items.

    :param definition:
        Specification definition for the associated value to cast.
    :param value:
        A loaded value to be cast into its boto client response value.
    :return:
        The cast version of the specified value that matches the format of
        the value as it would be returned in a boto client response.
    """
    return [cast(definition.get("member"), v) for v in value]


def _cast_string(
    definition: dict,
    value: typing.Any,
) -> typing.Union[str, StreamingBody]:
    """
    Converts a string botocore type into its formatted value. If the
    definition indicates that the string is returned in streaming format,
    a StreamingBody object is returned instead with the string value
    injected into the body via an InternalStreamer object that mimics the
    actual streaming behavior of a real StreamingBody response.

    :param definition:
        Specification definition for the associated value to cast.
    :param value:
        A loaded value to be cast into its boto client response value.
    :return:
        The cast version of the specified value that matches the format of
        the value as it would be returned in a boto client response.
    """
    output = str(value)
    if definition.get("streaming"):
        output = StreamingBody(InternalStreamer(output), len(output))
    return output


def _cast_blob(
    definition: dict,
    value: typing.Any,
) -> typing.Union[bytes, StreamingBody]:
    """
    Converts a blob botocore type into its formatted value. If the
    definition indicates that the blob is returned in streaming format,
    a StreamingBody object is returned instead with the bytes value
    injected into the body via an InternalStreamer object that mimics the
    actual streaming behavior of a real StreamingBody response.

    :param definition:
        Specification definition for the associated value to cast.
    :param value:
        A loaded value to be cast into its boto client response value.
    :return:
        The cast version of the specified value that matches the format of
        the value as it would be returned in a boto client response.
    """
    if isinstance(value, bytes):
        output = value
    else:
        output = str(value).encode()

    if definition.get("streaming"):
        output = StreamingBody(InternalStreamer(output), len(output))
    return output


def _cast_timestamp(
    definition: dict,
    value: typing.Union[float, int, str, datetime.date, datetime.datetime],
) -> datetime.datetime:
    """
    Converts a string date definition into a datetime as would be returned
    by the boto response. The dateutil library is used to parse the string
    for flexible representation. Additionally, an integer/float value can
    be specified, which will be treated as a unix timestamp. Note that
    boto returns timezone-aware datetime objects, so this loading process
    ensures that the returned datetime is timezone-aware. If no timezone
    was determined by the loading process, UTC is used by default.

    :param definition:
        Specification definition for the associated value to cast.
    :param value:
        A loaded value to be cast into its boto client response value.
    :return:
        The cast version of the specified value that matches the format of
        the value as it would be returned in a boto client response.
    """
    if isinstance(value, (int, float)):
        output = datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)
    elif isinstance(value, datetime.datetime):
        output = value
    elif isinstance(value, datetime.date):
        output = datetime.datetime(
            year=value.year,
            month=value.month,
            day=value.day,
            tzinfo=datetime.timezone.utc,
        )
    else:
        output = dateutil.parser.parse(value)

    if not output.tzinfo:
        return output.replace(tzinfo=datetime.timezone.utc)
    return output


def cast(definition: typing.Optional[dict], value: typing.Any) -> typing.Any:
    """
    Casts the raw mocked value into its equivalent boto response type as
    defined by the definition object for the value. For complex types, this
    function acts recursively.

    :param definition:
        Specification definition for the associated value to cast.
    :param value:
        A loaded value to be cast into its boto client response value.
    :return:
        The cast version of the specified value that matches the format of
        the value as it would be returned in a boto client response.
    """
    if definition is None:
        # If there is no definition because it does not exist, just return
        # the value as-is.
        return value

    data_type: typing.Optional[str] = definition.get("type")
    conversions = {
        "structure": _cast_structure,
        "list": _cast_list,
        "timestamp": _cast_timestamp,
        "string": _cast_string,
        "long": _cast_integer,
        "integer": _cast_integer,
        "blob": _cast_blob,
        "noop": _cast_noop,
    }
    caster: typing.Any = conversions.get(
        data_type or "noop",
        _cast_noop,
    )

    try:
        if isinstance(value, lobotomy.YamlModifier):
            return caster(definition, value.to_response_data())
        return caster(definition, value)
    except Exception as error:
        raise lobotomy.DataTypeError(
            f"""
            Failed to cast specified response data of type "{data_type}"
            for the value:
            {value}
            There may be an incompatibility between the value specified in
            the lobotomy configuration data for the response and the data type
            expected by the return of the boto response.
            """
        ) from error
