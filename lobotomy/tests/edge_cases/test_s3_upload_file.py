import lobotomy


@lobotomy.Patch()
def test_s3_upload_file(lobotomized: lobotomy.Lobotomy):
    """Should handle s3.upload_file correctly despite it being an augmentation."""
    lobotomized.data = {"clients": {"s3": {"upload_file": {}}}}
    session = lobotomized()
    client = session.client("s3")
    client.upload_file(Filename="foo", Bucket="bar", Key="baz")

    call = lobotomized.get_service_calls("s3", "upload_file")[0]
    assert call.request["Filename"] == "foo"
    assert call.request["Bucket"] == "bar"
    assert call.request["Key"] == "baz"
