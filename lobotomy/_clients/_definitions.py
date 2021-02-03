import datetime
import functools
import typing
from unittest.mock import MagicMock

from botocore.client import ClientMeta
from botocore.config import Config

import lobotomy
from lobotomy import _services
from lobotomy._clients import _casting
from lobotomy._clients import _validation


class Client:
    """
    Mocks AWS boto3.client behaviors that pull response data from data stored
    in configuration files.
    """

    def __init__(
        self,
        session: "lobotomy.Session",
        service_name: str,
        region_name: str = None,
        api_version: str = None,
        use_ssl: bool = True,
        verify: typing.Union[bool, str] = None,
        endpoint_url: str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        aws_session_token: str = None,
        config: Config = None,
    ):
        """Populate with the loaded scenario data."""
        self._service_name = service_name
        self._client_init_kwargs: dict = {
            "region_name": region_name,
            "api_version": api_version,
            "use_ssl": use_ssl,
            "verify": verify,
            "endpoint_url": endpoint_url,
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "aws_session_token": aws_session_token,
            "config": config,
        }
        self._calls: typing.List[lobotomy.ServiceCall] = []
        self._service: _services.Service = _services.load_definition(
            service_name,
        )
        self._session = session

        self.meta = ClientMeta(
            events=MagicMock(),
            client_config=config,
            endpoint_url=endpoint_url,
            service_model=MagicMock(),
            method_to_api_mapping={},
            partition="aws",
        )
        self.exceptions = MagicMock()
        self._registered_exceptions = {}
        for name in self._service.exceptions:
            new_type = type(name, (lobotomy.ClientError,), {})
            setattr(self.exceptions, name, new_type)
            self._registered_exceptions[name] = new_type

    def _call(self, called_method_name: str, *args, **kwargs):
        raw = self._session.lobotomy.pop_response(
            self._service_name,
            called_method_name,
        )
        method = self._service.lookup(called_method_name)
        request = _validation.validate_input(method, args, kwargs)
        response = _casting.cast(method.output, raw)

        service_call = lobotomy.ServiceCall(
            service=self._service_name,
            method=called_method_name,
            request=request,
            args=args,
            kwargs=kwargs,
            response=response,
        )

        self._session.lobotomy.record_call(service_call)
        self._calls.append(service_call)

        if "Error" in response:
            error = self._registered_exceptions.get(
                response["Error"]["Code"],
                lobotomy.ClientError,
            )()
            raise error.populate(**response["Error"])
        return response

    def __getattr__(self, item: str):
        """
        Retrieves response data for the given client call from the
        scenario data that defines the execution.
        """
        if not self._service.has(item):
            raise lobotomy.NoSuchMethod(
                f"""
                No boto/botocore definition found for "{self._service_name}{item}()".
                The version of botocore installed could be out of date, or newer
                and this service method has been removed. Please check the boto3
                documentation to confirm the existence of this service method.
                """
            )

        return functools.partial(self._call, item)

    def generate_presigned_url(
        self,
        ClientMethod: str,
        Params: typing.Dict[str, typing.Any] = None,
        ExpiresIn: int = 3600,
        HttpMethod: str = None,
    ):
        """
        Generate a presigned url given a client, its method, and arguments.

        https://docs.aws.amazon.com/STS/latest/APIReference/CommonParameters.html

        :param ClientMethod:
            The client method to presign for.
        :param Params:
            The parameters normally passed to ClientMethod.
        :param ExpiresIn:
            The number of seconds the presigned url is valid for. By default it
            expires in an hour (3600 seconds)
        :param HttpMethod:
            The http method to use on the generated url. By default, the http method
            is whatever is used in the method's model.
        """
        name = self._service_name
        action = "".join([w.capitalize() for w in ClientMethod.split("_")])
        version = self._client_init_kwargs["api_version"] or "2011-06-15"
        access = (
            self._client_init_kwargs["aws_access_key_id"]
            or self._session.get_credentials().access_key
        )
        region = self._client_init_kwargs["region_name"] or self._session.region_name
        now = (
            datetime.datetime.utcnow()
            .replace(microsecond=0)
            .astimezone(datetime.timezone.utc)
        )
        day = now.date().isoformat().replace("-", "")
        date = (
            now.isoformat("T").replace("+00:00", "Z").replace(":", "").replace("-", "")
        )
        url_parts = [
            f"https://{name}.amazonaws.com/",
            f"?Action={action}",
            f"&Version={version}",
            "&X-Amz-Algorithm=AWS4-HMAC-SHA256",
            f"&X-Amz-Credential={access}%2F{day}%2F{region}%2F{name}%2Faws4_request",
            f"&X-Amz-Date={date}",
            f"&X-Amz-Expires={ExpiresIn}",
            "&X-Amz-SignedHeaders=host",
            "&X-Amz-Security-Token=LobotomyFakeToken",
            "&X-Amz-Signature=lobotomyfakesignature",
        ]
        return "".join(url_parts)

    def get_paginator(self, item: str) -> MagicMock:
        """Mocks a single-page paginator response."""

        def _call(*args, **kwargs):
            return [self._call(item, *args, **kwargs)]

        paginator = MagicMock()
        paginator.paginate.side_effect = _call
        return paginator
