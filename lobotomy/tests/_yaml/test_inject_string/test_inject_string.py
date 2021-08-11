import pathlib

import lobotomy

directory = pathlib.Path(__file__).parent.absolute()


@lobotomy.patch(path=directory.joinpath("scenario.yaml"))
def test_inject_string(lobotomized: lobotomy.Lobotomy):
    """Should inject the external file as a string."""
    response = lobotomized().client("s3").get_object(Bucket="foo", Key="abc")
    assert response["Body"].read() == directory.joinpath("body.txt").read_bytes()
