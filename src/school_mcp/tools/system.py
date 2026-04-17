from typing import Literal
from ..client import SchoolClient


async def user_tool(
    client: SchoolClient,
    action: Literal["page", "create", "update", "delete", "reset_password"],
    id: int | None = None,
    page: int = 1,
    size: int = 10,
    keyword: str | None = None,
    payload: dict | None = None,
) -> dict:
    """系统用户管理。仅 ADMIN 可操作。后端无 get 接口（list 已含详情）。"""
    base = "/api/system/users"

    if action == "page":
        params: dict = {"page": page, "size": size}
        if keyword is not None:
            params["keyword"] = keyword
        return await client.request("GET", base, params=params)

    if action == "create":
        if not payload:
            raise ValueError("action=create 需要参数 payload")
        return await client.request("POST", base, json=payload)

    if action == "update":
        if id is None or not payload:
            raise ValueError("action=update 需要参数 id 和 payload")
        return await client.request("PUT", f"{base}/{id}", json=payload)

    if action == "delete":
        if id is None:
            raise ValueError("action=delete 需要参数 id")
        return await client.request("DELETE", f"{base}/{id}")

    if action == "reset_password":
        if id is None:
            raise ValueError("action=reset_password 需要参数 id")
        return await client.request("PUT", f"{base}/{id}/reset-password")

    raise ValueError(f"未知 action: {action}")
