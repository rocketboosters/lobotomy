import pytest

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
    assert len(lob.service_calls) == 1
    assert len(lob.get_service_calls("sts", "get_caller_identity")) == 1


@lobotomy.Patch()
def test_get_service_calls(lob: lobotomy.Lobotomy):
    """Should correctly retrieve service calls made."""
    lob.data = {"clients": {"sts": {"get_caller_identity": {"Account": "123"}}}}
    session = lob()
    client = session.client("sts")

    assert client.get_caller_identity()["Account"] == "123"
    assert client.get_caller_identity()["Account"] == "123", "Expected to work twice."

    assert len(lob.service_calls) == 2
    assert len(lob.get_service_calls("sts", "get_caller_identity")) == 2
    assert lob.get_service_call("sts", "get_caller_identity", 0)
    assert lob.get_service_call("sts", "get_caller_identity", 1)

    with pytest.raises(IndexError):
        lob.get_service_call("sts", "get_caller_identity", 2)


@lobotomy.Patch()
def test_creation_empty_added(lob: lobotomy.Lobotomy):
    """Should patch an empty lobotomy and then work after setting data manually."""
    lob.add_call("sts", "get_caller_identity", {"Account": "123"})
    session = lob()
    client = session.client("sts")
    assert client.get_caller_identity()["Account"] == "123"


@lobotomy.Patch()
def test_session_properties(lob: lobotomy.Lobotomy):
    """Should return the expected values for session properties."""
    session_data = {
        "profile_name": "foo-bar",
        "region_name": "us-north-1",
        "available_profiles": ["foo-bar", "baz"],
    }
    lob.data = {"session": session_data}
    session = lob()
    assert session.profile_name == "foo-bar"
    assert session.region_name == "us-north-1"
    assert session.available_profiles == ["foo-bar", "baz"]


@lobotomy.Patch()
def test_credentials(lob: lobotomy.Lobotomy):
    """Should return the expected values for session credentials."""
    credentials = {
        "method": "foo",
        "access_key": "A123",
        "secret_key": "123abc",
        "token": "foobar",
    }
    lob.data = {"session": {"credentials": credentials}}
    session = lob()
    observed = session.get_credentials()
    assert observed.method == "foo"
    assert observed.access_key == "A123"
    assert observed.secret_key == "123abc"
    assert observed.token == "foobar"

    frozen = observed.get_frozen_credentials()
    assert frozen.access_key == "A123"
    assert frozen.secret_key == "123abc"
    assert frozen.token == "foobar"


@lobotomy.Patch(client_overrides={"sts": {"foo": "bar"}})
def test_override(lob: lobotomy.Lobotomy):
    """Should return the override dictionary for the STS client."""
    session = lob()
    assert session.client("sts") == {"foo": "bar"}


@lobotomy.Patch()
def test_override_manual(lob: lobotomy.Lobotomy):
    """Should return the override dictionary for the STS client."""
    session = lob.add_client_override("sts", {"foo": "bar"})()
    assert session.client("sts") == {"foo": "bar"}


@lobotomy.Patch(client_overrides={"sts": {"foo": "bar"}})
def test_override_removed(lob: lobotomy.Lobotomy):
    """Should not return the override dictionary for the STS client if removed."""
    session = lob.remove_client_override("sts")()
    assert session.client("sts") != {"foo": "bar"}
    assert isinstance(session.client("sts"), lobotomy.Client)
