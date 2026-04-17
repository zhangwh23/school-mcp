import pytest
import respx
import httpx

from school_mcp.client import SchoolClient
from school_mcp.errors import BusinessError, HttpError, AuthError
from tests.conftest import make_jwt


@pytest.fixture
def login_token() -> str:
    return make_jwt(exp_in_seconds=3600)


def _login_response(token: str) -> httpx.Response:
    return httpx.Response(200, json={"code": 200, "data": {"token": token}})


@pytest.mark.asyncio
async def test_request_get_unwraps_data(config, login_token):
    async with respx.mock(base_url=config.api_base) as router:
        router.post("/api/auth/login").mock(return_value=_login_response(login_token))
        router.get("/api/students/1").mock(
            return_value=httpx.Response(200, json={
                "code": 200, "data": {"id": 1, "name": "张三"}
            })
        )

        client = SchoolClient(config)
        try:
            data = await client.request("GET", "/api/students/1")
        finally:
            await client.aclose()

        assert data == {"id": 1, "name": "张三"}


@pytest.mark.asyncio
async def test_request_business_error_raises(config, login_token):
    async with respx.mock(base_url=config.api_base) as router:
        router.post("/api/auth/login").mock(return_value=_login_response(login_token))
        router.post("/api/students").mock(
            return_value=httpx.Response(200, json={"code": 500, "message": "学号已存在"})
        )

        client = SchoolClient(config)
        try:
            with pytest.raises(BusinessError) as exc:
                await client.request("POST", "/api/students", json={"studentNo": "001"})
        finally:
            await client.aclose()
        assert "学号已存在" in str(exc.value)


@pytest.mark.asyncio
async def test_request_5xx_raises_http_error(config, login_token):
    async with respx.mock(base_url=config.api_base) as router:
        router.post("/api/auth/login").mock(return_value=_login_response(login_token))
        router.get("/api/students").mock(return_value=httpx.Response(503))

        client = SchoolClient(config)
        try:
            with pytest.raises(HttpError) as exc:
                await client.request("GET", "/api/students")
        finally:
            await client.aclose()
        assert "503" in str(exc.value)


@pytest.mark.asyncio
async def test_request_data_null_returns_success_dict(config, login_token):
    async with respx.mock(base_url=config.api_base) as router:
        router.post("/api/auth/login").mock(return_value=_login_response(login_token))
        router.delete("/api/students/1").mock(
            return_value=httpx.Response(200, json={"code": 200, "data": None})
        )

        client = SchoolClient(config)
        try:
            data = await client.request("DELETE", "/api/students/1")
        finally:
            await client.aclose()
        assert data == {"success": True}


@pytest.mark.asyncio
async def test_401_triggers_relogin_and_retry(config):
    token1 = make_jwt(exp_in_seconds=3600)
    token2 = make_jwt(exp_in_seconds=3600)
    tokens = iter([token1, token2])

    def login_resp(_):
        return httpx.Response(200, json={"code": 200, "data": {"token": next(tokens)}})

    call_count = {"n": 0}

    def students_resp(request: httpx.Request):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return httpx.Response(401, json={"code": 401, "message": "未登录"})
        return httpx.Response(200, json={"code": 200, "data": {"records": []}})

    async with respx.mock(base_url=config.api_base) as router:
        login_route = router.post("/api/auth/login").mock(side_effect=login_resp)
        router.get("/api/students").mock(side_effect=students_resp)

        client = SchoolClient(config)
        try:
            data = await client.request("GET", "/api/students")
        finally:
            await client.aclose()

        assert data == {"records": []}
        assert login_route.call_count == 2
        assert call_count["n"] == 2


@pytest.mark.asyncio
async def test_401_retry_still_401_raises_auth_error(config):
    token = make_jwt(exp_in_seconds=3600)

    async with respx.mock(base_url=config.api_base) as router:
        router.post("/api/auth/login").mock(
            return_value=httpx.Response(200, json={"code": 200, "data": {"token": token}})
        )
        router.get("/api/students").mock(
            return_value=httpx.Response(401, json={"code": 401, "message": "未登录"})
        )

        client = SchoolClient(config)
        try:
            with pytest.raises(AuthError) as exc:
                await client.request("GET", "/api/students")
        finally:
            await client.aclose()
        assert "401" in str(exc.value) or "认证失败" in str(exc.value)


@pytest.mark.asyncio
async def test_openapi_caches_within_ttl(config):
    spec = {"openapi": "3.0.1", "paths": {"/api/x": {}}}
    async with respx.mock(base_url=config.api_base) as router:
        openapi_route = router.get("/v3/api-docs").mock(
            return_value=httpx.Response(200, json=spec)
        )

        client = SchoolClient(config)
        try:
            r1 = await client.fetch_openapi()
            r2 = await client.fetch_openapi()
            r3 = await client.fetch_openapi()
        finally:
            await client.aclose()

        assert r1 == r2 == r3 == spec
        assert openapi_route.call_count == 1


@pytest.mark.asyncio
async def test_openapi_refetches_after_ttl_expires(config):
    from school_mcp.config import Config as Cfg
    short_cfg = Cfg(
        api_base=config.api_base, username=config.username,
        password=config.password, timeout=config.timeout,
        openapi_ttl=0,
    )
    spec = {"openapi": "3.0.1"}

    async with respx.mock(base_url=config.api_base) as router:
        openapi_route = router.get("/v3/api-docs").mock(
            return_value=httpx.Response(200, json=spec)
        )

        client = SchoolClient(short_cfg)
        try:
            await client.fetch_openapi()
            await client.fetch_openapi()
        finally:
            await client.aclose()

        assert openapi_route.call_count == 2
