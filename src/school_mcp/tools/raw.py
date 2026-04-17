from typing import Literal
from ..client import SchoolClient


async def list_apis_tool(
    client: SchoolClient,
    keyword: str | None = None,
    detail: bool = False,
) -> dict:
    """列出后端所有可用 API 接口。

    当 school_xxx 资源 tool 不能满足需求时，先调此 tool 查看接口清单，
    再用 school_call 调用具体接口。
    """
    spec = await client.fetch_openapi()
    paths = spec.get("paths", {}) or {}
    kw = keyword.lower() if keyword else None

    apis = []
    for path, methods in paths.items():
        for method, op in methods.items():
            if not isinstance(op, dict):
                continue
            summary = op.get("summary", "") or ""
            if kw and kw not in path.lower() and kw not in summary.lower():
                continue
            entry = {"path": path, "method": method.upper(), "summary": summary}
            if detail:
                entry["parameters"] = op.get("parameters", [])
                entry["requestBody"] = op.get("requestBody")
                entry["responses"] = op.get("responses")
            apis.append(entry)

    return {"apis": apis, "total": len(apis)}


async def call_tool(
    client: SchoolClient,
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
    path: str,
    query: dict | None = None,
    body: dict | None = None,
) -> dict:
    """通用 API 调用。仅当 school_xxx 资源 tool 无法满足时使用。

    建议先调 school_list_apis 确认接口存在和参数。
    """
    if not path.startswith("/api/"):
        raise ValueError("path 必须以 /api/ 开头")

    kwargs: dict = {}
    if query:
        kwargs["params"] = query
    if body is not None:
        kwargs["json"] = body
    return await client.request(method, path, **kwargs)
