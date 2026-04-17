import pytest
import respx
import httpx

from school_mcp.client import SchoolClient
from school_mcp.tools.raw import list_apis_tool, call_tool
from tests.conftest import make_jwt


@pytest.fixture
def login_token() -> str:
    return make_jwt(exp_in_seconds=3600)


def _login_response(token: str) -> httpx.Response:
    return httpx.Response(200, json={"code": 200, "data": {"token": token}})


SAMPLE_OPENAPI = {
    "openapi": "3.0.1",
    "paths": {
        "/api/students": {
            "get": {"summary": "学生列表", "parameters": [{"name": "page"}]},
            "post": {"summary": "新增学生", "requestBody": {}}
        },
        "/api/grades/export": {
            "get": {"summary": "导出成绩 Excel", "parameters": []}
        },
    }
}


@pytest.mark.asyncio
async def test_list_apis_default_summary_only(config):
    async with respx.mock(base_url=config.api_base) as router:
        router.get("/v3/api-docs").mock(return_value=httpx.Response(200, json=SAMPLE_OPENAPI))

        client = SchoolClient(config)
        try:
            result = await list_apis_tool(client)
        finally:
            await client.aclose()

        assert result["total"] == 3
        for item in result["apis"]:
            assert set(item.keys()) == {"path", "method", "summary"}


@pytest.mark.asyncio
async def test_list_apis_with_keyword(config):
    async with respx.mock(base_url=config.api_base) as router:
        router.get("/v3/api-docs").mock(return_value=httpx.Response(200, json=SAMPLE_OPENAPI))

        client = SchoolClient(config)
        try:
            result = await list_apis_tool(client, keyword="export")
        finally:
            await client.aclose()

        assert result["total"] == 1
        assert result["apis"][0]["path"] == "/api/grades/export"


@pytest.mark.asyncio
async def test_list_apis_keyword_matches_summary(config):
    async with respx.mock(base_url=config.api_base) as router:
        router.get("/v3/api-docs").mock(return_value=httpx.Response(200, json=SAMPLE_OPENAPI))

        client = SchoolClient(config)
        try:
            result = await list_apis_tool(client, keyword="新增")
        finally:
            await client.aclose()

        assert result["total"] == 1
        assert result["apis"][0]["method"] == "POST"


@pytest.mark.asyncio
async def test_list_apis_detail_includes_parameters(config):
    async with respx.mock(base_url=config.api_base) as router:
        router.get("/v3/api-docs").mock(return_value=httpx.Response(200, json=SAMPLE_OPENAPI))

        client = SchoolClient(config)
        try:
            result = await list_apis_tool(client, keyword="students", detail=True)
        finally:
            await client.aclose()

        assert any("parameters" in item for item in result["apis"])


@pytest.mark.asyncio
async def test_call_tool_get(config, login_token):
    async with respx.mock(base_url=config.api_base) as router:
        router.post("/api/auth/login").mock(return_value=_login_response(login_token))
        route = router.get("/api/grades/export").mock(
            return_value=httpx.Response(200, json={"code": 200, "data": {"url": "..."}})
        )

        client = SchoolClient(config)
        try:
            result = await call_tool(
                client, method="GET", path="/api/grades/export", query={"studentId": 1}
            )
        finally:
            await client.aclose()

        assert result == {"url": "..."}
        assert "studentId=1" in str(route.calls[0].request.url)


@pytest.mark.asyncio
async def test_call_tool_post_with_body(config, login_token):
    async with respx.mock(base_url=config.api_base) as router:
        router.post("/api/auth/login").mock(return_value=_login_response(login_token))
        router.post("/api/x").mock(
            return_value=httpx.Response(200, json={"code": 200, "data": None})
        )

        client = SchoolClient(config)
        try:
            result = await call_tool(
                client, method="POST", path="/api/x", body={"k": "v"}
            )
        finally:
            await client.aclose()

        assert result == {"success": True}


@pytest.mark.asyncio
async def test_call_tool_rejects_non_api_path(config):
    client = SchoolClient(config)
    try:
        with pytest.raises(ValueError, match="path 必须以 /api/ 开头"):
            await call_tool(client, method="GET", path="/v3/api-docs")
    finally:
        await client.aclose()
