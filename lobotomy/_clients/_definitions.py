import functools
import typing
from unittest.mock import MagicMock

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
        *args,
        **kwargs,
    ):
        """Populate with the loaded scenario data."""
        self._service_name = service_name
        self._client_init_args: tuple = args
        self._client_init_kwargs: dict = kwargs
        self._calls: typing.List[lobotomy.ServiceCall] = []
        self._service: _services.Service = _services.load_definition(
            service_name,
        )
        self._session = session

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

    def get_paginator(self, item: str) -> MagicMock:
        """Mocks a single-page paginator response."""

        def _call(*args, **kwargs):
            return [self._call(item, *args, **kwargs)]

        paginator = MagicMock()
        paginator.paginate.side_effect = _call
        return paginator
