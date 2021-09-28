import pathlib

import lobotomy

_directory = pathlib.Path(__file__).resolve().parent


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


@lobotomy.patch(_directory.joinpath("test_s3_select.yaml"))
def test_s3_select_from_yaml(lobotomized: lobotomy.Lobotomy):
    """Should correctly return S3 Select results."""
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
        {"Records": {"Payload": b'{"foo": "bar", "spam": 1000}'}},
        {"Records": {"Payload": b'{"foo": "baz", "spam": 2000}'}},
    ]
