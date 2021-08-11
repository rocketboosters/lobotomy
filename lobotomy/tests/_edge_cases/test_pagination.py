import lobotomy


@lobotomy.patch()
def test_pagination(lobotomized: lobotomy.Lobotomy):
    """Should paginate correctly by using only the first response."""
    lobotomized.add_call("s3", "list_objects_v2", {"Contents": [{"Key": "a"}]})
    lobotomized.add_call("s3", "list_objects_v2", {"Contents": [{"Key": "b"}]})

    session = lobotomized()
    client = session.client("s3")

    paginator = client.get_paginator("list_objects_v2")
    pages = []
    for page in paginator.paginate(Bucket="my-bucket"):
        pages.append(page)

    assert pages == [{"Contents": [{"Key": "a"}]}]
