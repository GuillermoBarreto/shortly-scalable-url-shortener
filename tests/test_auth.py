async def test_register_login_refresh_and_me(client):
    created = await client.post(
        "/api/v1/auth/register", json={"email": "user@example.com", "password": "strong-password"}
    )
    assert created.status_code == 201
    duplicate = await client.post(
        "/api/v1/auth/register", json={"email": "user@example.com", "password": "strong-password"}
    )
    assert duplicate.status_code == 409
    logged_in = await client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "strong-password"}
    )
    assert logged_in.status_code == 200
    tokens = logged_in.json()
    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.json()["email"] == "user@example.com"
    refreshed = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refreshed.status_code == 200


async def test_invalid_credentials_and_protected_route(client):
    assert (await client.get("/api/v1/links")).status_code == 401
    await client.post(
        "/api/v1/auth/register", json={"email": "user@example.com", "password": "strong-password"}
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "wrong"}
    )
    assert response.status_code == 401
