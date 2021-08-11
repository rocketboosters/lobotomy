import typing


class LobotomyError(Exception):
    """Base exception class for all lobotomy custom exceptions."""

    def __init__(self, message: str):
        """Create the generic lobotomy error with the given message."""
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
    An exception that mirrors the structure of a boto3/botocore exception.

    This is used to create errors without the added complexity of those actual exception
    classes.
    """

    def __init__(self, *args, **kwargs):
        """Create the error."""
        super(ClientError, self).__init__()
        self._code: typing.Optional[str] = None
        self._message: typing.Optional[str] = None

    @property
    def response(self) -> typing.Dict[str, typing.Any]:
        """Serialize boto response format for the object."""
        return {"Error": {"Code": self._code, "Message": self._message}}

    def populate(self, **kwargs) -> "ClientError":
        """Specify code and message for the client error."""
        self._code = kwargs.get("Code")
        self._message = kwargs.get("Message")
        return self
