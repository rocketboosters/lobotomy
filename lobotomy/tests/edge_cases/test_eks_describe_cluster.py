import lobotomy


@lobotomy.patch()
def test_eks_describe_cluster(lobotomized: lobotomy.Lobotomy):
    """Should return result without error."""
    lobotomized.add_call(
        "eks",
        "describe_cluster",
        response={
            "name": "cluster-name",
            "arn": "arn:aws:eks:us-west-2:123456:cluster/cluster-name",
            "certificateAuthority": {"data": "fakecertificatedata="},
        },
    )
    response = lobotomized().client("eks").describe_cluster("cluster-name")
    assert response["arn"] == "arn:aws:eks:us-west-2:123456:cluster/cluster-name"
