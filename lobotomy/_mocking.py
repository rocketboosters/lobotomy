import pathlib
import typing
from unittest.mock import patch as mock_patch

import lobotomy as lbm


class Patch:
    """
    A patch decorator class that will behave like the unittest.mock.patch
    specifically for the boto3.Session object, replacing it in the test
    with the Lobotomy session factory that will be used to replace the normal
    boto3 calls with the lobotomized ones.
    """

    def __init__(
        self,
        path: typing.Union[None, str, pathlib.Path] = None,
        data: dict = None,
        prefix: typing.Union[None, str, typing.Iterable[str]] = None,
        patch_path: str = "boto3.Session",
        client_overrides: typing.Dict[str, typing.Any] = None,
    ):
        """
        Create a patch instance.

        :param path:
            Path to a configuration file containing the lobotomy data to use
            in mock calls during the lifetime of this patch. This can be the
            default value if a data value is set instead.
        :param data:
            Dictionary containing the lobotomy data to use in mock calls
            during the lifetime of this patch. This can be the default None
            value if a path value is set instead.
        :param prefix:
            An optional key or multi-key prefix within the path-loaded data
            object where the lobotomy data resides. Use this when the
            configuration file for the test has a broader scope.
        :param patch_path:
            The targeted patch target, which defaults to 'boto3.Session'.
            This can be used to override that value for cases where a
            different patch target is desirable.
        :param client_overrides:
            Optional dictionary containing mappings of service names to clients
            that should be used in place of lobotomy clients during the lifecycle
            of this lobotomy patch. Useful for mixing lobotomy clients with other
            mocking clients in complex testing scenarios.
        """
        self.data = data
        self.path = path
        self.prefix = prefix
        self.patch_path = patch_path
        self.client_overrides = client_overrides
        self._context_patch: typing.Any = None

    def _make_lobotomy(self) -> "lbm.Lobotomy":
        """
        Creates the lobotomy object to be used during the patch lifetime.
        This has to be created with each call to prevent multiple scenario
        executions for the same test function.
        """
        if self.data is not None:
            return lbm.Lobotomy(
                self.data.copy(),
                client_overrides=self.client_overrides,
            )
        elif self.path:
            return lbm.Lobotomy.from_file(
                self.path,
                prefix=self.prefix,
                client_overrides=self.client_overrides,
            )

        return lbm.Lobotomy(client_overrides=self.client_overrides)

    def __call__(self, caller: typing.Callable):
        """
        Calls the patching decorator that wraps the test function with
        a patch of the boto3.Session class.
        """
        return mock_patch(self.patch_path, new_callable=self._make_lobotomy)(caller)

    def __enter__(self):
        """..."""
        p = mock_patch(self.patch_path, new_callable=self._make_lobotomy)
        self._context_patch = p
        return p.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._context_patch is None:
            return True
        return self._context_patch.__exit__(exc_type, exc_val, exc_tb)


patch = Patch
