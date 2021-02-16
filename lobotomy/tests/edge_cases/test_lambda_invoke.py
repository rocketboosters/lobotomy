import lobotomy


@lobotomy.patch()
def test_lambda_invoke(lobotomized: lobotomy.Lobotomy):
    """Should return a StreamingBody for the payload."""
    lobotomized.add_call("lambda", "invoke")
    response = lobotomized().client("lambda").invoke(FunctionName="foo")
    assert b"..." == response["Payload"].read()
