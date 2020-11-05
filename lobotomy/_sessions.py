import json
import pathlib
import typing

import toml
import yaml
from botocore.session import Session as BotocoreSession

import lobotomy


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
        self.lobotomy: Lobotomy = source_lobotomy

        self._constructed = {
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "aws_session_token": aws_session_token,
            "region_name": region_name,
            "botocore_session": botocore_session,
            "profile_name": profile_name,
        }
        self._definition = source_lobotomy.get_session_data()
        self._data = {
            **self._definition,
            **{k: v for k, v in self._constructed.items() if v is not None},
        }
        self._clients = {}

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

    def __init__(self, data: typing.Dict[str, typing.Any] = None):
        self.data = data or {}

    def __call__(
        self,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        aws_session_token: str = None,
        region_name: str = None,
        botocore_session: BotocoreSession = None,
        profile_name: str = None,
    ) -> "Session":
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
        data = self.data.get("session", self.data.get("sessions")) or {}
        if not isinstance(data, dict):
            return data.pop(0)
        return data

    def get_response(self, service_name: str, method_name: str) -> dict:
        response = self.data.get("clients", {}).get(service_name, {}).get(method_name)
        if response is None:
            raise ValueError(f"No response available for {service_name}.{method_name}")
        if isinstance(response, list):
            return response.pop(0)
        return typing.cast(dict, response)

    @classmethod
    def from_file(
        cls,
        path: typing.Union[str, pathlib.Path],
        prefix: typing.Union[str, typing.Iterable[str]] = None,
    ) -> "Lobotomy":
        contents = pathlib.Path(path).absolute().read_text()

        if path.name.endswith((".yaml", ".yml")):
            data = yaml.safe_load(contents)
        elif path.name.endswith(".toml"):
            data = toml.loads(contents)
        else:
            data = json.loads(contents)

        return cls(data=_get_within(data, prefix))


def _get_within(
    data: dict,
    prefix: typing.Union[None, str, typing.Iterable[str]],
) -> dict:
    if not prefix:
        return data

    parts = prefix.split(".") if isinstance(prefix, str) else prefix
    for key in parts:
        data = data.get(key, {})
    return data
