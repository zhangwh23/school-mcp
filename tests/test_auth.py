import pytest
import respx
import httpx

from school_mcp.auth import AuthManager
from school_mcp.errors import AuthError
from tests.conftest import make_jwt


@pytest.mark.asyncio
async def test_first_call_triggers_login(config, http_client):
    token = make_jwt(exp_in_seconds=3600)
    async with respx.mock(base_url=config.api_base) as router:
        login_route = router.post("/api/auth/login").mock(
            return_value=httpx.Response(200, json={
                "code": 200, "message": "ok",
                "data": {"token": token, "username": "testuser", "realName": "测试", "roles": ["ADMIN"]}
            })
        )

        auth = AuthManager(config, http_client)
        got = await auth.get_token()

        assert got == token
        assert login_route.call_count == 1


@pytest.mark.asyncio
async def test_login_failure_raises_auth_error(config, http_client):
    async with respx.mock(base_url=config.api_base) as router:
        router.post("/api/auth/login").mock(
            return_value=httpx.Response(200, json={"code": 401, "message": "用户名或密码错误"})
        )

        auth = AuthManager(config, http_client)
        with pytest.raises(AuthError) as exc:
            await auth.get_token()
        assert "用户名或密码错误" in str(exc.value)


@pytest.mark.asyncio
async def test_login_http_error_raises_auth_error(config, http_client):
    async with respx.mock(base_url=config.api_base) as router:
        router.post("/api/auth/login").mock(return_value=httpx.Response(500))

        auth = AuthManager(config, http_client)
        with pytest.raises(AuthError) as exc:
            await auth.get_token()
        assert "500" in str(exc.value)


@pytest.mark.asyncio
async def test_valid_token_skips_login(config, http_client):
    token = make_jwt(exp_in_seconds=3600)
    async with respx.mock(base_url=config.api_base) as router:
        login_route = router.post("/api/auth/login").mock(
            return_value=httpx.Response(200, json={
                "code": 200, "data": {"token": token}
            })
        )

        auth = AuthManager(config, http_client)
        await auth.get_token()
        await auth.get_token()
        await auth.get_token()

        assert login_route.call_count == 1


@pytest.mark.asyncio
async def test_expiring_token_triggers_refresh(config, http_client):
    expiring_token = make_jwt(exp_in_seconds=30)
    fresh_token = make_jwt(exp_in_seconds=3600)
    tokens = iter([expiring_token, fresh_token])

    def respond(_):
        return httpx.Response(200, json={"code": 200, "data": {"token": next(tokens)}})

    async with respx.mock(base_url=config.api_base) as router:
        login_route = router.post("/api/auth/login").mock(side_effect=respond)

        auth = AuthManager(config, http_client)
        first = await auth.get_token()
        second = await auth.get_token()

        assert first == expiring_token
        assert second == fresh_token
        assert login_route.call_count == 2


@pytest.mark.asyncio
async def test_unparseable_token_falls_back_to_5min(config, http_client):
    async with respx.mock(base_url=config.api_base) as router:
        router.post("/api/auth/login").mock(
            return_value=httpx.Response(200, json={
                "code": 200, "data": {"token": "opaque-token-xyz"}
            })
        )

        auth = AuthManager(config, http_client)
        token = await auth.get_token()

        assert token == "opaque-token-xyz"
        import time
        assert 290 <= (auth._exp - time.time()) <= 305


@pytest.mark.asyncio
async def test_concurrent_get_token_only_logs_in_once(config, http_client):
    import asyncio as _asyncio
    token = make_jwt(exp_in_seconds=3600)

    async def slow_login(request):
        await _asyncio.sleep(0.05)
        return httpx.Response(200, json={"code": 200, "data": {"token": token}})

    async with respx.mock(base_url=config.api_base) as router:
        login_route = router.post("/api/auth/login").mock(side_effect=slow_login)

        auth = AuthManager(config, http_client)
        results = await _asyncio.gather(*(auth.get_token() for _ in range(10)))

        assert all(r == token for r in results)
        assert login_route.call_count == 1


@pytest.mark.asyncio
async def test_force_refresh_always_logs_in(config, http_client):
    token1 = make_jwt(exp_in_seconds=3600)
    token2 = make_jwt(exp_in_seconds=3600)
    tokens = iter([token1, token2])

    def respond(_):
        return httpx.Response(200, json={"code": 200, "data": {"token": next(tokens)}})

    async with respx.mock(base_url=config.api_base) as router:
        login_route = router.post("/api/auth/login").mock(side_effect=respond)

        auth = AuthManager(config, http_client)
        first = await auth.get_token()
        forced = await auth.force_refresh()

        assert first == token1
        assert forced == token2
        assert login_route.call_count == 2
