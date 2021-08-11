from lobotomy._services._definitions import Method  # noqa: F401
from lobotomy._services._definitions import Service  # noqa: F401


def load_definition(service_name: str) -> "Service":
    """Load client definition data for the associated AWS service."""
    return Service(service_name)
