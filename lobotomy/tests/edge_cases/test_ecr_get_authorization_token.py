import lobotomy

ecr_client_data = {
    "get_authorization_token": {
        "authorizationData": [
            {
                "authorizationToken": "...",
                "expiresAt": "2020-11-04T20:06:29.048640Z",
                "proxyEndpoint": "...",
            }
        ]
    }
}


@lobotomy.Patch(data={"clients": {"ecr": ecr_client_data}})
def test_ecr_get_authorization_token(lobotomized: lobotomy.Lobotomy):
    """Should allow registryIds as an input argument."""
    client = lobotomized().client("ecr")
    response = client.get_authorization_token(registryIds=["123"])
    assert response["authorizationData"][0]["authorizationToken"] == "..."
