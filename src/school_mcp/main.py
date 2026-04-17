"""MCP server 入口：初始化 client、注册 tools、启动 stdio 循环。"""
import asyncio
import functools
import logging
import sys
from typing import Literal

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from .client import SchoolClient
from .config import Config
from .errors import AuthError, BusinessError, HttpError, SchoolMcpError
from .tools.clazz import clazz_tool
from .tools.course import course_tool
from .tools.dashboard import dashboard_tool
from .tools.grade import grade_tool
from .tools.raw import call_tool, list_apis_tool
from .tools.student import student_tool
from .tools.system import user_tool
from .tools.teacher import teacher_tool


def _convert_errors(func):
    """把内部异常统一转为 ToolError 给 MCP 协议层。"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AuthError as e:
            raise ToolError(f"认证失败，请检查 SCHOOL_USERNAME/SCHOOL_PASSWORD: {e}")
        except BusinessError as e:
            raise ToolError(str(e))
        except HttpError as e:
            raise ToolError(f"后端服务异常，请稍后重试: {e}")
        except httpx.TimeoutException:
            raise ToolError("请求超时，请检查 SCHOOL_API_BASE 是否可达")
        except httpx.ConnectError as e:
            raise ToolError(f"无法连接后端: {e}")
        except SchoolMcpError as e:
            raise ToolError(str(e))
    return wrapper


def main() -> None:
    config = Config.from_env()

    logging.basicConfig(
        level=config.log_level,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    log = logging.getLogger("school-mcp")
    log.info(f"school-mcp starting, backend={config.api_base}")

    client = SchoolClient(config)
    mcp = FastMCP("school")

    @mcp.tool()
    @_convert_errors
    async def school_student(
        action: Literal["page", "get", "create", "update", "delete"],
        id: int | None = None,
        page: int = 1,
        size: int = 10,
        keyword: str | None = None,
        class_id: int | None = None,
        payload: dict | None = None,
    ) -> dict:
        """学生管理。

        actions:
          - page: 分页查询。可选 keyword(模糊搜索), class_id(按班级筛选)
          - get: 按 ID 查询。必填 id
          - create: 新增。必填 payload，字段参考 StudentDTO
                    例 {"studentNo":"2024001","name":"张三","gender":1,"classId":3}
          - update: 更新。必填 id 和 payload
          - delete: 删除（逻辑）。必填 id

        权限：create/update/delete 需要 ADMIN；page/get 需要 ADMIN 或 TEACHER。
        """
        return await student_tool(client, action, id, page, size, keyword, class_id, payload)

    @mcp.tool()
    @_convert_errors
    async def school_teacher(
        action: Literal["page", "get", "create", "update", "delete"],
        id: int | None = None,
        page: int = 1,
        size: int = 10,
        keyword: str | None = None,
        payload: dict | None = None,
    ) -> dict:
        """教师管理。actions: page/get/create/update/delete。"""
        return await teacher_tool(client, action, id, page, size, keyword, payload)

    @mcp.tool()
    @_convert_errors
    async def school_clazz(
        action: Literal["page", "get", "create", "update", "delete", "assign_students"],
        id: int | None = None,
        page: int = 1,
        size: int = 10,
        keyword: str | None = None,
        student_ids: list[int] | None = None,
        payload: dict | None = None,
    ) -> dict:
        """班级管理（注意包名是 clazz，URL 是 /api/classes）。

        actions: page/get/create/update/delete/assign_students。
        assign_students 需要 id 和 student_ids（学生 ID 列表）。
        """
        return await clazz_tool(client, action, id, page, size, keyword, student_ids, payload)

    @mcp.tool()
    @_convert_errors
    async def school_course(
        action: Literal["page", "get", "create", "update", "delete"],
        id: int | None = None,
        page: int = 1,
        size: int = 10,
        keyword: str | None = None,
        teacher_id: int | None = None,
        class_id: int | None = None,
        payload: dict | None = None,
    ) -> dict:
        """课程管理。actions: page/get/create/update/delete。"""
        return await course_tool(client, action, id, page, size, keyword, teacher_id, class_id, payload)

    @mcp.tool()
    @_convert_errors
    async def school_grade(
        action: Literal["page", "create", "update", "statistics"],
        id: int | None = None,
        page: int = 1,
        size: int = 10,
        student_id: int | None = None,
        course_id: int | None = None,
        semester: str | None = None,
        payload: dict | None = None,
    ) -> dict:
        """成绩管理。

        actions:
          - page: 分页查询。可选 student_id / course_id / semester 过滤
          - create: 新增成绩。必填 payload
          - update: 更新成绩。必填 id 和 payload
          - statistics: 学期成绩统计。必填 semester

        后端无 get/delete 接口（删错重录或更新即可）。
        """
        return await grade_tool(client, action, id, page, size, student_id, course_id, semester, payload)

    @mcp.tool()
    @_convert_errors
    async def school_user(
        action: Literal["page", "create", "update", "delete", "reset_password"],
        id: int | None = None,
        page: int = 1,
        size: int = 10,
        keyword: str | None = None,
        payload: dict | None = None,
    ) -> dict:
        """系统用户管理。仅 ADMIN 可操作。

        actions: page/create/update/delete/reset_password。
        reset_password 必填 id，将密码重置为后端默认值。
        """
        return await user_tool(client, action, id, page, size, keyword, payload)

    @mcp.tool()
    @_convert_errors
    async def school_dashboard() -> dict:
        """获取首页统计数据：学生/教师/班级/课程总数等。"""
        return await dashboard_tool(client)

    @mcp.tool()
    @_convert_errors
    async def school_list_apis(
        keyword: str | None = None,
        detail: bool = False,
    ) -> dict:
        """列出后端所有可用 API。

        Args:
          keyword: 按路径或 summary 关键字过滤（不区分大小写）
          detail: True 返回完整参数定义；False 只返回 path+method+summary
        """
        return await list_apis_tool(client, keyword, detail)

    @mcp.tool()
    @_convert_errors
    async def school_call(
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
        path: str,
        query: dict | None = None,
        body: dict | None = None,
    ) -> dict:
        """通用 API 调用。仅当 school_xxx 资源 tool 无法满足时使用。

        建议先调 school_list_apis 确认接口存在和参数。path 必须以 /api/ 开头。
        """
        return await call_tool(client, method, path, query, body)

    try:
        mcp.run(transport="stdio")
    finally:
        try:
            asyncio.run(client.aclose())
        except Exception:
            pass


if __name__ == "__main__":
    main()
