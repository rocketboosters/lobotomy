import typing

from lobotomy import _services


def add_service_response(
    lobotomy_data: dict,
    method: "_services.Method",
    response: typing.Any = None,
) -> None:
    if "clients" not in lobotomy_data:
        lobotomy_data["clients"] = {}

    if method.service.name not in lobotomy_data["clients"]:
        lobotomy_data["clients"][method.service.name] = {}

    service_data = lobotomy_data["clients"][method.service.name]
    response_type = method.output.get("type", "structure")
    if response is None:
        new_response = method.configuration_output
    else:
        new_response = response

    if method.name not in service_data:
        if response_type == "list":
            # List entries confuse the side effect behavior of popping
            # responses off the list. To avoid that the list responses
            # are added as list items.
            service_data[method.name] = [new_response]
        else:
            service_data[method.name] = new_response
        return

    existing = service_data[method.name]
    if isinstance(existing, dict):
        service_data[method.name] = [existing, new_response]
    else:
        service_data[method.name] = existing + [new_response]
