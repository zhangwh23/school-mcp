from ..client import SchoolClient


async def dashboard_tool(client: SchoolClient) -> dict:
    """获取首页统计数据：学生/教师/班级/课程总数等。"""
    return await client.request("GET", "/api/dashboard/stats")
