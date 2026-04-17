from typing import Literal
from ..client import SchoolClient


async def course_tool(
    client: SchoolClient,
    action: Literal["page", "get", "create", "update", "delete"],
    id: int | None = None,
    page: int = 1,
    size: int = 10,
    keyword: str | None = None,
    teacher_id: int | None = None,
    class_id: int | None = None,
    payload: dict | None = None,
) -> dict:
    """课程管理。"""
    base = "/api/courses"

    if action == "page":
        params: dict = {"page": page, "size": size}
        if keyword is not None:
            params["keyword"] = keyword
        if teacher_id is not None:
            params["teacherId"] = teacher_id
        if class_id is not None:
            params["classId"] = class_id
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

    raise ValueError(f"未知 action: {action}")
