async def test_responses_include_browser_security_headers(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


async def test_auth_responses_cannot_be_cached(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "not-the-password"},
    )

    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"


async def test_invalid_content_length_is_rejected(client):
    response = await client.get("/health", headers={"content-length": "invalid"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Content-Length"}


async def test_oversized_request_is_rejected_before_routing(client):
    response = await client.post(
        "/api/v1/auth/login",
        headers={"content-length": "999999999"},
        content=b"{}",
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "Request body is too large"}
