import lobotomy


@lobotomy.patch()
def test_s3_select(lobotomized: lobotomy.Lobotomy):
    """Should correctly return S3 Select results."""
    lobotomized.add_call(
        "s3",
        "select_object_content",
        {
            "Payload": [
                {"Records": {"Payload": "a"}},
                {"Records": {"Payload": "b"}},
                {"Records": {"Payload": "c"}},
            ]
        },
    )

    response = (
        lobotomized()
        .client("s3")
        .select_object_content(
            Bucket="foo",
            Key="bar/baz.file",
            InputSerialization={"Parquet": {}},
            Expression="SELECT * FROM S3Object LIMIT 100",
            ExpressionType="SQL",
            OutputSerialization={"JSON": {"RecordDelimiter": "\n"}},
        )
    )
    observed = list(response["Payload"])
    assert observed == [
        {"Records": {"Payload": b"a"}},
        {"Records": {"Payload": b"b"}},
        {"Records": {"Payload": b"c"}},
    ]
