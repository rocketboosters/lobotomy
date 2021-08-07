import dataclasses
import pathlib
import typing
from unittest.mock import MagicMock

from botocore.session import Session as BotocoreSession

import lobotomy
from lobotomy import _fio
from lobotomy import _mutator
from lobotomy import _services


def _get_key(
    source: typing.Optional[dict],
    key: typing.Any,
    default: typing.Any = None,
) -> typing.Any:
    """Fetch the value of the key in the source or the default if not present."""
    return (source or {}).get(key, default)


@dataclasses.dataclass(frozen=True)
class ServiceCall:
    """Data structure for recording service calls made on clients."""

    #: Name of the service in which this call was made.
    service: str
    #: Name of the method within the specified service in which this call was made.
    method: str
    #: A normalized request dictionary that contains key/value pairs for each of
    #: the arguments passed into the method call. This combines args and kwargs together
    #: into a representative "kwargs" dictionary to avoid having to manually lookup
    #: method arguments manually in a combined args/kwargs fashion.
    request: typing.Dict[str, typing.Any]
    #: Positional arguments specified in the service method call. These are also
    #: available by keyword in the "request" attribute of this ServiceCall instance.
    args: typing.Tuple[typing.Any, ...]
    #: Keyword arguments specified in the service method call. These are also
    #: available in the "request" attribute of this ServiceCall instance as well.
    kwargs: typing.Dict[str, typing.Any]
    #: The lobotomized response that was returned with this invocation as specified by
    #: the loaded lobotomy data.
    response: typing.Union[list, dict, str, None]


class ReadOnlyCredentials(typing.NamedTuple):
    """Data structure that matches ReadOnlyCredentials from botocore library."""

    access_key: str
    secret_key: str
    token: typing.Optional[str]


class Credentials:
    """
    Mock botocore Credentials object used by Session.get_credentials during
    lobotomy tests.
    """

    def __init__(self, data: dict = None):
        """Stores configuration data for access."""
        self._data = data or {}

    @property
    def method(self) -> str:
        """Authentication method by which credentials were loaded."""
        return self._data.get("method", "manual")

    @property
    def access_key(self) -> str:
        """AWS access key for the associated session."""
        return self._data.get("access_key", "A123LOBOTOMY")

    @property
    def secret_key(self) -> str:
        """AWS secret key for the associated session."""
        return self._data.get("secret_key", "lobotomysecretkey")

    @property
    def token(self) -> typing.Optional[str]:
        """Optional AWS access token for the associated session."""
        return self._data.get("token")

    def get_frozen_credentials(self) -> "ReadOnlyCredentials":
        """A named-tuple form of the credentials for the associated session."""
        return ReadOnlyCredentials(self.access_key, self.secret_key, self.token)


class Session:
    """
    Mock boto3.Session object to use in place of the real one during lobotomy
    tests.
    """

    def __init__(
        self,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        aws_session_token: str = None,
        region_name: str = None,
        botocore_session: BotocoreSession = None,
        profile_name: str = None,
        source_lobotomy: "Lobotomy" = None,
    ):
        self.lobotomy: Lobotomy = source_lobotomy or Lobotomy()
        self.events = MagicMock()

        self._constructed = {
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "aws_session_token": aws_session_token,
            "region_name": region_name,
            "botocore_session": botocore_session,
            "profile_name": profile_name,
        }
        self._definition = self.lobotomy.get_session_data()
        self._data = {
            **self._definition,
            **{k: v for k, v in self._constructed.items() if v is not None},
        }
        self._clients: typing.Dict[str, "lobotomy.Client"] = {}

    @property
    def profile_name(self) -> typing.Optional[str]:
        """Optional name of the AWS profile used for the session if set."""
        return self._data.get("profile_name")

    @property
    def region_name(self) -> typing.Optional[str]:
        """Optional explicit AWS region used for the session if set."""
        return self._data.get("region_name")

    @property
    def available_profiles(self) -> typing.List[str]:
        """List of AWS profiles available for use in the session."""
        return self._data.get("available_profiles") or []

    def get_credentials(self) -> "Credentials":
        """Retrieves the credentials associated with the session."""
        return Credentials(self._data.get("credentials") or {})

    def client(self, service_name: str, *args, **kwargs) -> "lobotomy.Client":
        """
        Creates a lobotomy client object for the specified service. Each
        service-client is a singleton such that subsequent calls for the
        same service name will return the same object.
        """
        override = self.lobotomy.get_client_override(service_name)
        if override is not None:
            return override

        if service_name not in self._clients:
            self._clients[service_name] = lobotomy.Client(
                self,
                service_name,
                *args,
                **kwargs,
            )
        return self._clients[service_name]


class Lobotomy:
    """
    Factory replacement class for boto3.Session that generates mock session
    objects during lobotomy tests.
    """

    def __init__(
        self,
        data: typing.Dict[str, typing.Any] = None,
        client_overrides: typing.Dict[str, typing.Any] = None,
    ):
        self.data = data or {}
        self._client_overrides = client_overrides or {}
        self._service_calls: typing.List[ServiceCall] = []

    @property
    def service_calls(self) -> typing.Tuple["ServiceCall", ...]:
        """A list of the service calls that have been made so far."""
        return tuple(self._service_calls)

    def get_service_call(
        self,
        service_name: str,
        method_name: str,
        index: int = 0,
    ) -> "ServiceCall":
        """
        Finds and returns the Nth service call made for the given method for inspection
        and assertion during test evaluation as specified by the index.

        :param service_name:
            Name of the AWS boto3 service in which the method call being added resides.
        :param method_name:
            Name of the AWS boto3 method to be called for this response within the
            specified service.
        :param index:
            Specifies the Nth service call made for the given service and method names
            to be returned. This is a zero-indexed value.
        :return:
            Nth-specified service call for the given service and method names. If no
            such call exists, an IndexError will be raised.
        """
        return self.get_service_calls(service_name, method_name)[index]

    def get_service_calls(
        self,
        service_name: str,
        method_name: str,
    ) -> typing.List["ServiceCall"]:
        """
        Finds and returns a list containing all service calls made for the given method
        for inspection and assertion during test evaluation.

        :param service_name:
            Name of the AWS boto3 service in which the method call being added resides.
        :param method_name:
            Name of the AWS boto3 method to be called for this response within the
            specified service.
        """
        return [
            s
            for s in self._service_calls
            if s.service == service_name and s.method == method_name
        ]

    def add_client_override(self, service_name: str, client: typing.Any) -> "Lobotomy":
        """
        Add an override client that will be returned instead of a lobotomy client
        within the scope of this Lobotomy's lifecycle.

        :param service_name:
            Name of the AWS boto service of the client to be overridden.
        :param client:
            The replacement client object that will be returned instead of a lobotomy
            client.
        """
        self._client_overrides[service_name] = client
        return self

    def remove_client_override(self, service_name: str) -> "Lobotomy":
        """
        Removes an overridden client if such an override exists. Will do nothing if
        the override does not currently exist.

        :param service_name:
            Name of the AWS boto service of the client to be removed as an override.
        """
        if service_name in self._client_overrides:
            del self._client_overrides[service_name]
        return self

    def get_client_override(self, service_name: str) -> typing.Any:
        """
        Retrieves an override client if it exists.

        :param service_name:
            Name of the AWS boto service for which to fetch an override client.
        """
        return self._client_overrides.get(service_name)

    def add_call(
        self,
        service_name: str,
        method_name: str,
        response: typing.Any = None,
    ) -> "Lobotomy":
        """
        Adds a method call response to the stored data. Operates in the same fashion
        as the CLI, in that additional adds will convert a single call into a list of
        calls.

        :param service_name:
            Name of the AWS boto3 service in which the method call being added resides.
        :param method_name:
            Name of the AWS boto3 method to be called for this response within the
            specified service.
        :param response:
            Boto3 response object for the given method call within the service.
        """
        service = _services.load_definition(service_name)
        method = service.lookup(method_name)
        _mutator.add_service_response(self.data, method, response)
        return self

    def __call__(
        self,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        aws_session_token: str = None,
        region_name: str = None,
        botocore_session: BotocoreSession = None,
        profile_name: str = None,
    ) -> "Session":
        """
        Mimics the boto3.Session() constructor as a lobotomized session factory.
        The arguments to this method match the arguments to the boto3.Session()
        constructor signature and are stored within the lobotomized session as
        part of the duck-typed interface.
        """
        return Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=region_name,
            botocore_session=botocore_session,
            profile_name=profile_name,
            source_lobotomy=self,
        )

    def get_session_data(self) -> dict:
        """Retrieves the lobotomized configuration data assocated with the session."""
        data = self.data.get("session", self.data.get("sessions")) or {}
        if not isinstance(data, dict):
            return data.pop(0)
        return data

    def record_call(self, service_call: "ServiceCall") -> None:
        """
        Records a service call made from a client in the list of overall service
        calls for the lobotomized environment. This is meant to be called by
        lobotomy.Clients only.

        :param service_call:
            Service call to record within the lobotomy instance.
        """
        self._service_calls.append(service_call)

    def pop_response(
        self,
        service_name: str,
        method_name: str,
        arguments: typing.Dict[str, typing.Any] = None,
    ) -> typing.Any:
        """
        Retrieves the response data for the given service and method name
        combination from the lobotomy data. If such a response does not
        exist, an error is raised instead.

        :param service_name:
            Name of the boto3 service in which the method call lookup is being made.
        :param method_name:
            Name of the method within the boto3 service for which to lookup a response.
        :param arguments:
            The arguments supplied to the lobotomized request, which are needed when
            the call data is a callable object.
        :return:
            A response object containing the lobotomized response for the given
            service method call.
        """
        response = self.data.get("clients", {}).get(service_name, {}).get(method_name)

        if response is None:
            raise lobotomy.NoResponseFound(
                f"""
                No response set for "{service_name}.{method_name}()" in the
                configuration data for this lobotomy. Check to ensure the
                method call was included in the source configuration data.
                """
            )

        if isinstance(response, list):
            if not response:
                raise lobotomy.NoResponseFound(
                    f"""
                    No more responses set for "{service_name}.{method_name}()"
                    in the configuration data for this lobotomy. All specified
                    responses have been returned already.
                    """
                )
            response = response.pop(0)

        if callable(response):
            args = _get_key(arguments, "args") or tuple()
            kwargs = _get_key(arguments, "kwargs") or {}
            return response(*args, **kwargs)

        return response

    @classmethod
    def from_file(
        cls,
        path: typing.Union[str, pathlib.Path],
        prefix: typing.Union[str, typing.Iterable[str]] = None,
        client_overrides: typing.Dict[str, typing.Any] = None,
    ) -> "Lobotomy":
        """
        Create a patch instance.

        :param path:
            Path to a configuration file containing the lobotomy data to use
            in mock calls during the lifetime of this patch. This can be the
            default value if a data value is set instead.
        :param prefix:
            An optional key or multi-key prefix within the path-loaded data
            object where the lobotomy data resides. Use this when the
            configuration file for the test has a broader scope.
        :param client_overrides:
            Optional dictionary containing mappings of service names to clients
            that should be used in place of lobotomy clients during the lifecycle
            of this lobotomy patch. Useful for mixing lobotomy clients with other
            mocking clients in complex testing scenarios.
        """
        p = pathlib.Path(path)
        return cls(data=_fio.read(p, prefix), client_overrides=client_overrides)
