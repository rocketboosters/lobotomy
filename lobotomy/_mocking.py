import pathlib
import typing
from unittest.mock import patch

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
        """
        self.data = data
        self.path = path
        self.prefix = prefix
        self.patch_path = patch_path

    def __call__(self, caller: typing.Callable):
        """
        Calls the patching decorator that wraps the test function with
        a patch of the boto3.Session class.
        """
        if self.data is not None:
            lobotomy = lbm.Lobotomy(self.data)
        elif self.path:
            lobotomy = lbm.Lobotomy.from_file(self.path, prefix=self.prefix)
        else:
            lobotomy = lbm.Lobotomy()

        return patch(self.patch_path, new_callable=lambda: lobotomy)(caller)
