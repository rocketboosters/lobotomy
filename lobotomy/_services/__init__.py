from lobotomy._services._definitions import Method  # noqa
from lobotomy._services._definitions import Service  # noqa


def load_definition(service_name: str) -> "Service":
    """Loads client definition data for the associated AWS service."""
    return Service(service_name)
