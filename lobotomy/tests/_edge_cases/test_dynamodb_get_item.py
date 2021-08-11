import lobotomy


@lobotomy.Patch()
def test_dynamodb_get_item(lobotomized: lobotomy.Lobotomy):
    """Should handle dynamodb.get_item without recursion errors."""
    lobotomized.data = {"clients": {"dynamodb": {"get_item": {}}}}
    session = lobotomized()
    client = session.client("dynamodb")
    client.get_item(TableName="foo", Key={"pk": {"S": "spam"}, "sk": {"S": "ham"}})

    call = lobotomized.get_service_calls("dynamodb", "get_item")[0]
    assert call.request["TableName"] == "foo"
