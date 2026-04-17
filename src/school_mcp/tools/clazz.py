from typing import Literal
from ..client import SchoolClient


async def clazz_tool(
    client: SchoolClient,
    action: Literal["page", "get", "create", "update", "delete", "assign_students"],
    id: int | None = None,
    page: int = 1,
    size: int = 10,
    keyword: str | None = None,
    student_ids: list[int] | None = None,
    payload: dict | None = None,
) -> dict:
    """班级管理。后端路径 /api/classes（注意：包名是 clazz 但 URL 是 classes）。"""
    base = "/api/classes"

    if action == "page":
        params: dict = {"page": page, "size": size}
        if keyword is not None:
            params["keyword"] = keyword
        return await client.request("GET", base, params=params)

    if action == "get":
        if id is None:
            raise ValueError("action=get 需要参数 id")
        return await client.request("GET", f"{base}/{id}")

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

    if action == "assign_students":
        if id is None or student_ids is None:
            raise ValueError("action=assign_students 需要参数 id 和 student_ids")
        return await client.request("POST", f"{base}/{id}/students", json=student_ids)

    raise ValueError(f"未知 action: {action}")
