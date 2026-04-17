import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """从环境变量读取的不可变配置。"""

    api_base: str
    username: str
    password: str
    timeout: float = 30.0
    log_level: str = "INFO"
    openapi_ttl: int = 300

    @classmethod
    def from_env(cls) -> "Config":
        required = ("SCHOOL_API_BASE", "SCHOOL_USERNAME", "SCHOOL_PASSWORD")
        missing = [k for k in required if not os.getenv(k)]
        if missing:
            raise SystemExit(f"缺少必填环境变量: {', '.join(missing)}")

        return cls(
            api_base=os.environ["SCHOOL_API_BASE"].rstrip("/"),
            username=os.environ["SCHOOL_USERNAME"],
            password=os.environ["SCHOOL_PASSWORD"],
            timeout=float(os.getenv("SCHOOL_TIMEOUT", "30")),
            log_level=os.getenv("SCHOOL_LOG_LEVEL", "INFO"),
            openapi_ttl=int(os.getenv("SCHOOL_OPENAPI_TTL", "300")),
        )
