import lobotomy


@lobotomy.patch()
def test_generate_presigned_url(lobotomized: lobotomy.Lobotomy):
    """Should generate a mock presigned URL."""
    client = lobotomized().client("sts")
    result = client.generate_presigned_url("get_caller_identity")
    assert result.startswith("https://sts.")
