from lobotomy._services._definitions import Service
from lobotomy._services._definitions import Method


def load_definition(service_name: str) -> "Service":
    """Loads client definition data for the associated AWS service."""
    return _definitions.Service(service_name)
