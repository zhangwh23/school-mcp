import pytest
import httpx

from school_mcp.config import Config


@pytest.fixture
def config() -> Config:
    """测试用配置。"""
    return Config(
        api_base="http://test-backend:8080",
        username="testuser",
        password="testpass",
        timeout=5.0,
    )


@pytest.fixture
async def http_client(config: Config) -> httpx.AsyncClient:
    """共享 httpx AsyncClient，关闭由 pytest 自动管理。"""
    async with httpx.AsyncClient(base_url=config.api_base, timeout=config.timeout) as client:
        yield client


def make_jwt(exp_in_seconds: int = 3600) -> str:
    """生成一个测试用 JWT，包含指定的过期时间。"""
    import time
    import jwt as _jwt
    payload = {"sub": "testuser", "exp": int(time.time()) + exp_in_seconds}
    return _jwt.encode(payload, "test-secret", algorithm="HS256")
