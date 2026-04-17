from typing import Literal
from ..client import SchoolClient


async def grade_tool(
    client: SchoolClient,
    action: Literal["page", "create", "update", "statistics"],
    id: int | None = None,
    page: int = 1,
    size: int = 10,
    student_id: int | None = None,
    course_id: int | None = None,
    semester: str | None = None,
    payload: dict | None = None,
) -> dict:
    """成绩管理。后端无 get/delete 接口（成绩按 update/重新录入处理）。"""
    base = "/api/grades"

    if action == "page":
        params: dict = {"page": page, "size": size}
        if student_id is not None:
            params["studentId"] = student_id
        if course_id is not None:
            params["courseId"] = course_id
        if semester is not None:
            params["semester"] = semester
        return await client.request("GET", base, params=params)

    if action == "create":
        if not payload:
            raise ValueError("action=create 需要参数 payload")
        return await client.request("POST", base, json=payload)

    if action == "update":
        if id is None or not payload:
            raise ValueError("action=update 需要参数 id 和 payload")
        return await client.request("PUT", f"{base}/{id}", json=payload)

    if action == "statistics":
        if not semester:
            raise ValueError("action=statistics 需要参数 semester")
        return await client.request("GET", f"{base}/statistics", params={"semester": semester})

    raise ValueError(f"未知 action: {action}")
