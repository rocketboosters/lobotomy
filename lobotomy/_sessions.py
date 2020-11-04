import json
import pathlib
import typing

import toml
import yaml
from botocore.session import Session as BotocoreSession

import lobotomy


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
        source_lobotomy: 'Lobotomy' = None,
    ):
        self.lobotomy: Lobotomy = source_lobotomy

        self._constructed = {
            'aws_access_key_id': aws_access_key_id,
            'aws_secret_access_key': aws_secret_access_key,
            'aws_session_token': aws_session_token,
            'region_name': region_name,
            'botocore_session': botocore_session,
            'profile_name': profile_name,
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
        return self._data.get('profile_name')

    @property
    def region_name(self) -> typing.Optional[str]:
        """Optional explicit AWS region used for the session if set."""
        return self._data.get('region_name')

    @property
    def available_profiles(self) -> typing.List[str]:
        """List of AWS profiles available for use in the session."""
        return self._data.get('available_profiles') or []

    def client(self, service_name: str, *args, **kwargs) -> 'lobotomy.Client':
        """
        Creates a lobotomy client object for the specified service. Each
        service-client is a singleton such that subsequent calls for the
        same service name will return the same object.
        """
        if service_name not in self._clients:
            self._clients[service_name] = lobotomy.Client(
                self, service_name, *args, **kwargs,
            )
        return self._clients[service_name]


class Lobotomy:
    """
    Factory replacement class for boto3.Session that generates mock session
    objects during lobotomy tests.
    """

    def __init__(self, data: typing.Dict[str, typing.Any]):
        self._data = data

    def __call__(
        self,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        aws_session_token: str = None,
        region_name: str = None,
        botocore_session: BotocoreSession = None,
        profile_name: str = None,
    ) -> 'Session':
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
        data = self._data.get('session', self._data.get('sessions')) or {}
        if not isinstance(data, dict):
            return data.pop(0)
        return data

    def get_response(self, service_name: str, method_name: str) -> dict:
        response = (
            self._data.get('clients', {}).get(service_name, {}).get(method_name)
        )
        if response is None:
            raise ValueError(
                f'No response available for {service_name}.{method_name}'
            )
        if isinstance(response, list):
            return response.pop(0)
        return typing.cast(dict, response)

    @classmethod
    def from_file(
        cls,
        path: typing.Union[str, pathlib.Path],
        prefix: typing.Union[str, typing.Iterable[str]] = None,
    ) -> 'Lobotomy':
        contents = pathlib.Path(path).absolute().read_text()

        if path.name.endswith(('.yaml', '.yml')):
            data = yaml.safe_load(contents)
        elif path.name.endswith('.toml'):
            data = toml.loads(contents)
        else:
            data = json.loads(contents)

        return cls(data=_get_within(data, prefix))


def _get_within(
    data: dict, prefix: typing.Union[None, str, typing.Iterable[str]],
) -> dict:
    if not prefix:
        return data

    parts = prefix.split('.') if isinstance(prefix, str) else prefix
    for key in parts:
        data = data.get(key, {})
    return data
