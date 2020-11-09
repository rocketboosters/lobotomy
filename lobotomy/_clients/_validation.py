import typing

from lobotomy import _services


def validate_input(
    method: "_services.Method",
    request_args: typing.Iterable[typing.Any],
    request_kwargs: typing.Dict[str, typing.Any],
) -> None:
    """
    Compares the request made to its botocore definition to raise assertion
    errors if there are missing required arguments or if there are extraneous
    unknown arguments for the top-level request calls.

    Future work here would also look at required arguments hierarchically as
    well as use some of the patterns and mins/maxes specified by the botocore
    definition to confirm that the values given are also valid.

    :param method:
        Method definition object for the method that was called.
    :param request_args:
        Positional arguments made to the method call.
    :param request_kwargs:
        Keyword arguments made to the method call.
    """
    definition = method.input
    keys = list(definition["members"].keys())
    request = {
        **{keys[i]: a for i, a in enumerate(request_args)},
        **(request_kwargs or {}),
    }

    specified_keys = request.keys()
    required = set(definition.get("required", []))
    assert required <= set(
        specified_keys
    ), f"""
        Missing required arguments {required - set(specified_keys)}
        on {method.service.name}.{method.name}.
        """

    unknown_keys = set(
        [k for k in (set(specified_keys) - set(keys)) if not k.startswith("_")]
    )
    assert not unknown_keys, f"""
        Unknown arguments {unknown_keys} found on call to
        {method.service.name}.{method.name}.
        """
