from datetime import UTC, datetime, timedelta


async def test_anonymous_creation_and_redirect_records_analytics(client):
    created = await client.post(
        "/api/v1/links",
        json={"original_url": "https://example.com/article", "custom_alias": "article-one"},
    )
    assert created.status_code == 201
    link = created.json()
    redirected = await client.get(
        f"/{link['short_code']}",
        follow_redirects=False,
        headers={"user-agent": "Mozilla/5.0", "referer": "https://news.example"},
    )
    assert redirected.status_code == 307
    assert redirected.headers["location"] == "https://example.com/article"


async def test_url_and_alias_validation(client):
    assert (
        await client.post("/api/v1/links", json={"original_url": "javascript:alert(1)"})
    ).status_code == 422
    assert (
        await client.post("/api/v1/links", json={"original_url": "file:///etc/passwd"})
    ).status_code == 422
    assert (
        await client.post(
            "/api/v1/links",
            json={"original_url": "https://example.com", "custom_alias": "analytics"},
        )
    ).status_code == 422
    assert (
        await client.post(
            "/api/v1/links",
            json={"original_url": "https://example.com", "custom_alias": "bad alias"},
        )
    ).status_code == 422


async def test_duplicate_alias(client):
    body = {"original_url": "https://example.com", "custom_alias": "my-alias"}
    assert (await client.post("/api/v1/links", json=body)).status_code == 201
    assert (await client.post("/api/v1/links", json=body)).status_code == 409


async def test_unknown_expired_and_disabled_links(client, auth):
    assert (await client.get("/missing", follow_redirects=False)).status_code == 404
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    created = (
        await client.post(
            "/api/v1/links",
            headers=auth,
            json={"original_url": "https://example.com", "expires_at": future},
        )
    ).json()
    disabled = await client.patch(
        f"/api/v1/links/{created['id']}", headers=auth, json={"is_active": False}
    )
    assert disabled.status_code == 200
    response = await client.get(f"/{created['short_code']}", follow_redirects=False)
    assert response.status_code == 410 and response.json()["reason"] == "disabled"


async def test_crud_ownership_and_analytics(client, auth):
    created = (
        await client.post(
            "/api/v1/links",
            headers=auth,
            json={"original_url": "https://example.com", "title": "Example"},
        )
    ).json()
    listed = await client.get("/api/v1/links", headers=auth)
    assert listed.json()["total"] == 1
    second = await client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "password": "a-secure-password"},
    )
    other = {"Authorization": f"Bearer {second.json()['access_token']}"}
    assert (await client.get(f"/api/v1/links/{created['id']}", headers=other)).status_code == 404
    await client.get(f"/{created['short_code']}", follow_redirects=False)
    analytics = await client.get(f"/api/v1/links/{created['id']}/analytics", headers=auth)
    assert analytics.status_code == 200
    assert analytics.json()["link"]["total_clicks"] == 1
    stats = await client.get("/api/v1/dashboard/stats", headers=auth)
    assert stats.json()["total_clicks"] == 1
    assert (await client.delete(f"/api/v1/links/{created['id']}", headers=auth)).status_code == 204
    assert (await client.get(f"/api/v1/links/{created['id']}", headers=auth)).status_code == 404


async def test_qr_code(client, auth):
    link = (
        await client.post(
            "/api/v1/links", headers=auth, json={"original_url": "https://example.com"}
        )
    ).json()
    response = await client.get(f"/api/v1/links/{link['id']}/qr", headers=auth)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")
