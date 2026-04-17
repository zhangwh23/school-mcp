import pytest
import respx
import httpx

from school_mcp.client import SchoolClient
from school_mcp.tools.student import student_tool
from tests.conftest import make_jwt


@pytest.fixture
def login_token() -> str:
    return make_jwt(exp_in_seconds=3600)


def _login_response(token: str) -> httpx.Response:
    return httpx.Response(200, json={"code": 200, "data": {"token": token}})


@pytest.mark.asyncio
async def test_student_page_with_filters(config, login_token):
    async with respx.mock(base_url=config.api_base) as router:
        router.post("/api/auth/login").mock(return_value=_login_response(login_token))
        page_route = router.get("/api/students").mock(
            return_value=httpx.Response(200, json={
                "code": 200, "data": {"records": [{"id": 1}], "total": 1, "size": 10, "current": 1}
            })
        )

        client = SchoolClient(config)
        try:
            result = await student_tool(
                client, action="page", page=1, size=10, keyword="张", class_id=3
            )
        finally:
            await client.aclose()

        assert result["records"] == [{"id": 1}]
        call = page_route.calls[0]
        assert "page=1" in str(call.request.url)
        assert "size=10" in str(call.request.url)
        assert "keyword=" in str(call.request.url)
        assert "classId=3" in str(call.request.url)


@pytest.mark.asyncio
async def test_student_get_requires_id(config, login_token):
    client = SchoolClient(config)
    try:
        with pytest.raises(ValueError, match="action=get 需要参数 id"):
            await student_tool(client, action="get")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_student_create(config, login_token):
    async with respx.mock(base_url=config.api_base) as router:
        router.post("/api/auth/login").mock(return_value=_login_response(login_token))
        create_route = router.post("/api/students").mock(
            return_value=httpx.Response(200, json={"code": 200, "data": None})
        )

        client = SchoolClient(config)
        try:
            result = await student_tool(
                client, action="create",
                payload={"studentNo": "2024001", "name": "张三", "gender": 1, "classId": 3}
            )
        finally:
            await client.aclose()

        assert result == {"success": True}
        assert create_route.calls[0].request.method == "POST"


@pytest.mark.asyncio
async def test_student_update(config, login_token):
    async with respx.mock(base_url=config.api_base) as router:
        router.post("/api/auth/login").mock(return_value=_login_response(login_token))
        router.put("/api/students/5").mock(
            return_value=httpx.Response(200, json={"code": 200, "data": None})
        )

        client = SchoolClient(config)
        try:
            result = await student_tool(
                client, action="update", id=5, payload={"name": "李四"}
            )
        finally:
            await client.aclose()

        assert result == {"success": True}


@pytest.mark.asyncio
async def test_student_delete(config, login_token):
    async with respx.mock(base_url=config.api_base) as router:
        router.post("/api/auth/login").mock(return_value=_login_response(login_token))
        router.delete("/api/students/9").mock(
            return_value=httpx.Response(200, json={"code": 200, "data": None})
        )

        client = SchoolClient(config)
        try:
            result = await student_tool(client, action="delete", id=9)
        finally:
            await client.aclose()

        assert result == {"success": True}


@pytest.mark.asyncio
async def test_student_invalid_action(config):
    client = SchoolClient(config)
    try:
        with pytest.raises(ValueError, match="未知 action"):
            await student_tool(client, action="bulk_import")
    finally:
        await client.aclose()
