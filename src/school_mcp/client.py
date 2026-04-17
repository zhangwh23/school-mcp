import time
import httpx

from .auth import AuthManager
from .config import Config
from .errors import AuthError, BusinessError, HttpError


class SchoolClient:
    """统一 HTTP 客户端：注入 token、解包 Result、401 重试、OpenAPI 缓存。"""

    def __init__(self, config: Config):
        self._config = config
        self._http = httpx.AsyncClient(base_url=config.api_base, timeout=config.timeout)
        self._auth = AuthManager(config, self._http)
        self._openapi_cache: dict | None = None
        self._openapi_cached_at: float = 0.0

    async def aclose(self) -> None:
        await self._http.aclose()

    async def request(self, method: str, path: str, **kwargs) -> dict | list | None:
        token = await self._auth.get_token()
        resp = await self._send(method, path, token, **kwargs)

        if resp.status_code == 401:
            token = await self._auth.force_refresh()
            resp = await self._send(method, path, token, **kwargs)
            if resp.status_code == 401:
                raise AuthError("重试后仍 401，认证失败")

        return self._unwrap(resp)

    async def fetch_openapi(self) -> dict:
        now = time.time()
        if self._openapi_cache and (now - self._openapi_cached_at) < self._config.openapi_ttl:
            return self._openapi_cache
        resp = await self._http.get("/v3/api-docs")
        if resp.status_code != 200:
            raise HttpError(f"拉取 OpenAPI 失败 HTTP {resp.status_code}")
        self._openapi_cache = resp.json()
        self._openapi_cached_at = now
        return self._openapi_cache

    async def _send(self, method: str, path: str, token: str, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        return await self._http.request(method, path, headers=headers, **kwargs)

    def _unwrap(self, resp: httpx.Response) -> dict | list | None:
        if resp.status_code >= 500:
            raise HttpError(f"后端错误 HTTP {resp.status_code}")
        try:
            body = resp.json()
        except Exception as e:
            raise HttpError(f"响应不是合法 JSON: {e}") from e

        if body.get("code") != 200:
            raise BusinessError(body.get("message", "未知业务错误"))

        data = body.get("data")
        if data is None:
            return {"success": True}
        return data
