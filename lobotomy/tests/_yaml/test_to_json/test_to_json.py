import pathlib

import lobotomy

directory = pathlib.Path(__file__).parent.absolute()


@lobotomy.patch(path=directory.joinpath("simple.yaml"))
def test_to_json(lobotomized: lobotomy.Lobotomy):
    """Should inject JSON string."""
    response = lobotomized().client("secretsmanager").get_secret_value(SecretId="a")
    assert response["SecretString"] == '{"foo": "bar", "spam": 42}'


@lobotomy.patch(path=directory.joinpath("list.yaml"))
def test_to_json_list(lobotomized: lobotomy.Lobotomy):
    """Should inject JSON string."""
    response = lobotomized().client("secretsmanager").get_secret_value(SecretId="a")
    assert response["SecretString"] == '["bar", 42]'


@lobotomy.patch(path=directory.joinpath("nested.yaml"))
def test_to_json_nested(lobotomized: lobotomy.Lobotomy):
    """Should inject JSON string in a nested fashion."""
    response = lobotomized().client("secretsmanager").get_secret_value(SecretId="a")
    expected = '{"foo": "bar", "spam": 42, "ham": "[\\"hello\\", \\"world\\"]"}'
    assert response["SecretString"] == expected
