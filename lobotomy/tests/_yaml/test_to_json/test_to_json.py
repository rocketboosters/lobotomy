import pathlib

import lobotomy

directory = pathlib.Path(__file__).parent.absolute()


@lobotomy.patch(path=directory.joinpath("scenario.yaml"))
def test_to_json(lobotomized: lobotomy.Lobotomy):
    """Should inject JSON string."""
    response = lobotomized().client("secretsmanager").get_secret_value(SecretId="a")
    assert response["SecretString"] == '{"foo": "bar", "spam": 42}'
