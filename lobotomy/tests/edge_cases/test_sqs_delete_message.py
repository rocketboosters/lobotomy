import lobotomy


@lobotomy.Patch()
def test_sqs_delete_message(lobotomized: lobotomy.Lobotomy):
    """
    Should handle sqs.delete_message without error despite edge case
    configuration in botocore service method definitions where the return
    structure has no members.
    """
    lobotomized.add_call("sqs", "delete_message")
    lobotomized().client("sqs").delete_message(
        QueueUrl="https://sqs.us-west-2.amazonaws.com/123/my-queue",
        ReceiptHandle="fake-receipt-handle",
    )
    assert lobotomized.get_service_call("sqs", "delete_message") is not None
