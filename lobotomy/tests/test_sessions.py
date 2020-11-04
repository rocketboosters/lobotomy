import lobotomy


def test_creation_empty():
    """Should create an empty lobotomy and then work after setting data manually."""
    lob = lobotomy.Lobotomy()
    lob.data = {"clients": {"sts": {"get_caller_identity": {"Account": "123"}}}}
    session = lob()
    client = session.client("sts")
    assert client.get_caller_identity()["Account"] == "123"


@lobotomy.Patch()
def test_creation_empty_patched(lob: lobotomy.Lobotomy):
    """Should patch an empty lobotomy and then work after setting data manually."""
    lob.data = {"clients": {"sts": {"get_caller_identity": {"Account": "123"}}}}
    session = lob()
    client = session.client("sts")
    assert client.get_caller_identity()["Account"] == "123"
