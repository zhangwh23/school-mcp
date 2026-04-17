class SchoolMcpError(Exception):
    """所有 school-mcp 自定义异常的基类。"""


class AuthError(SchoolMcpError):
    """认证相关错误：登录失败、token 重试后仍 401。"""


class BusinessError(SchoolMcpError):
    """后端业务错误：Result.code != 200。"""


class HttpError(SchoolMcpError):
    """HTTP 5xx 或网络层错误。"""
