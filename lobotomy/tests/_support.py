from unittest.mock import MagicMock


def make_path(
    data: str,
    file_format: str = "json",
    exists: bool = True,
):
    """Create a mocked pathlib.Path object to return and use during testing."""
    path = MagicMock()
    path.name = f"foo.{file_format}"
    path.exists.return_value = exists
    path.read_text.return_value = data
    path.expanduser.return_value = path
    path.absolute.return_value = path
    return path
