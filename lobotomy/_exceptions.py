import typing


class LobotomyError(Exception):
    """Base exception class for all lobotomy custom exceptions."""

    def __init__(self, message: str):
        super(LobotomyError, self).__init__(message)


class NoResponseFound(LobotomyError):
    """Error raised when no response was found for the given method call."""

    pass


class NoSuchMethod(LobotomyError):
    """Error raised when a service method definition cannot be found."""

    pass


class DataTypeError(LobotomyError):
    """Error raised during casting of data types that fails."""

    pass


class RequestValidationError(LobotomyError):
    """Error raised when validation of the request arguments fails for a method call."""

    pass


class ClientError(Exception):
    """
    An exception that mirrors the structure of a boto3/botocore exception
    without the added complexity of those actual exception classes.
    """

    def __init__(self, *args, **kwargs):
        super(ClientError, self).__init__()
        self._code: typing.Optional[str] = None
        self._message: typing.Optional[str] = None

    @property
    def response(self) -> typing.Dict[str, typing.Any]:
        return {"Error": {"Code": self._code, "Message": self._message}}

    def populate(self, **kwargs) -> "ClientError":
        self._code = kwargs.get("Code")
        self._message = kwargs.get("Message")
        return self
