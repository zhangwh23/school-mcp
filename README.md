# school-mcp

[school 校园管理系统](https://github.com/zhangwh/school) 的 MCP 服务，让 Claude / Claude Code 等 AI 客户端能通过自然语言调用后端 API。

## 前置要求

1. **uv** 工具

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **可访问的 school 后端**
   - 后端必须开启 OpenAPI 文档（已支持，见 school 仓库的相关 commit）
   - 后端 `SCHOOL_API_BASE` 网络可达

3. **登录账号**
   - 已有效的 username + password

## 配置（Claude Code）

编辑 Claude Code 的 MCP 配置（通常在 `~/.claude/mcp.json` 或客户端设置）：

```json
{
  "mcpServers": {
    "school": {
      "command": "uvx",
      "args": [
        "--refresh",
        "--from",
        "git+https://github.com/zhangwh23/school-mcp.git@main",
        "school-mcp"
      ],
      "env": {
        "SCHOOL_API_BASE": "http://your-backend:8080",
        "SCHOOL_USERNAME": "admin",
        "SCHOOL_PASSWORD": "your-password"
      }
    }
  }
}
```

> `--refresh` 让 uvx 每次启动都拉取 main 分支最新代码；想要更新时**重启 Claude Code 客户端**或在会话中 reconnect MCP 即可。

## 环境变量

| 变量 | 必填 | 默认 | 说明 |
|---|---|---|---|
| `SCHOOL_API_BASE` | ✅ | — | 后端地址，例 `http://localhost:8080` |
| `SCHOOL_USERNAME` | ✅ | — | 登录账号 |
| `SCHOOL_PASSWORD` | ✅ | — | 登录密码 |
| `SCHOOL_TIMEOUT` | ❌ | `30` | HTTP 超时（秒） |
| `SCHOOL_LOG_LEVEL` | ❌ | `INFO` | DEBUG / INFO / WARNING / ERROR |
| `SCHOOL_OPENAPI_TTL` | ❌ | `300` | OpenAPI 缓存秒数 |

## 提供的 Tools

| Tool | 用途 |
|---|---|
| `school_student` | 学生 CRUD + 分页 |
| `school_teacher` | 教师 CRUD + 分页 |
| `school_clazz` | 班级 CRUD + 分页 + 学生分配 |
| `school_course` | 课程 CRUD + 分页 |
| `school_grade` | 成绩录入 / 更新 / 分页 / 统计 |
| `school_user` | 系统用户管理（仅 ADMIN） |
| `school_dashboard` | 首页统计数据 |
| `school_list_apis` | 列出后端所有 API（兜底发现） |
| `school_call` | 通用 HTTP 调用（兜底执行） |

## 使用示例

> 用户："帮我查三年二班的所有学生"

Claude 会自动：
1. `school_clazz(action="page", keyword="三年二班")` 找班级 ID
2. `school_student(action="page", class_id=找到的ID, size=100)` 拉学生
3. 用人话回复

> 用户："新增学生张三，学号 2024001，三年二班"

Claude 会调用 `school_student(action="create", payload={...})`。

## 故障排查

| 现象 | 原因 / 处理 |
|---|---|
| 启动时 `缺少必填环境变量` | 检查 mcpServers 配置的 env 是否完整 |
| 调用 tool 报"认证失败" | 账号/密码错误，或后端账号被禁 |
| 调用 tool 报"无法连接后端" | 检查 `SCHOOL_API_BASE` 是否可达，VPN 是否开着 |
| reconnect 后仍是旧代码 | 关闭 Claude Code 完全退出再开，或检查是否带了 `--refresh` |
| 列出的 API 缺失新接口 | 等最多 5 分钟（OpenAPI 缓存 TTL）或重启 MCP |

## 本地开发

```bash
git clone https://github.com/zhangwh23/school-mcp.git
cd school-mcp
uv sync --group dev

# 跑测试
uv run pytest -v

# 本地直连后端调试
SCHOOL_API_BASE=http://localhost:8080 \
  SCHOOL_USERNAME=admin \
  SCHOOL_PASSWORD=admin123 \
  uv run school-mcp
```
