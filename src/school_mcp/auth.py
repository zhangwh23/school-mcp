import asyncio
import time
import jwt
import httpx

from .config import Config
from .errors import AuthError


class AuthManager:
    """JWT token 管理：登录、过期检查、主动+被动刷新。"""

    REFRESH_THRESHOLD = 60  # 距过期还剩多少秒时主动刷新

    def __init__(self, config: Config, http: httpx.AsyncClient):
        self._config = config
        self._http = http
        self._token: str | None = None
        self._exp: float = 0.0
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        if self._is_valid():
            return self._token  # type: ignore[return-value]
        async with self._lock:
            if self._is_valid():
                return self._token  # type: ignore[return-value]
            await self._login()
        return self._token  # type: ignore[return-value]

    async def force_refresh(self) -> str:
        async with self._lock:
            await self._login()
        return self._token  # type: ignore[return-value]

    def _is_valid(self) -> bool:
        return self._token is not None and (self._exp - time.time()) > self.REFRESH_THRESHOLD

    async def _login(self) -> None:
        try:
            resp = await self._http.post(
                "/api/auth/login",
                json={"username": self._config.username, "password": self._config.password},
            )
        except httpx.HTTPError as e:
            raise AuthError(f"登录请求失败: {e}") from e

        if resp.status_code != 200:
            raise AuthError(f"登录失败 HTTP {resp.status_code}: {resp.text[:200]}")

        body = resp.json()
        if body.get("code") != 200:
            raise AuthError(f"登录被拒: {body.get('message')}")

        self._token = body["data"]["token"]
        try:
            payload = jwt.decode(self._token, options={"verify_signature": False})
            self._exp = float(payload.get("exp", 0))
        except jwt.PyJWTError:
            self._exp = time.time() + 300
