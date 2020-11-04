from unittest.mock import MagicMock
from unittest.mock import patch

import lobotomy


@patch("os.path.getctime")
@lobotomy.Patch()
@patch("os.path.getmtime")
def test_multiple_patches(
    os_path_getmtime: MagicMock,
    lobotomized: lobotomy.Lobotomy,
    os_path_getctime: MagicMock,
):
    """Should pass the arguments in the expected patch order."""
    assert str(os_path_getctime).find("getctime") > 0
    assert isinstance(lobotomized, lobotomy.Lobotomy)
    assert str(os_path_getmtime).find("getmtime") > 0
