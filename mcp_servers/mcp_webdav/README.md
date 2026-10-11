# mcp-webdav

WebDAV 文件管理 MCP 服务器，基于 [webdav4](https://github.com/pavdmyt/webdav4)。

## 配置（环境变量）

| 环境变量 | 必填 | 默认 | 说明 |
|---|---|---|---|
| `WEBDAV_URL` | 是 | — | WebDAV 服务基础 URL，如 `https://dav.jianguoyun.com/dav/` |
| `WEBDAV_USERNAME` | 否 | — | Basic Auth 用户名（需与 `WEBDAV_PASSWORD` 同时设置） |
| `WEBDAV_PASSWORD` | 否 | — | Basic Auth 密码（需与 `WEBDAV_USERNAME` 同时设置） |
| `WEBDAV_TIMEOUT` | 否 | `30` | 请求超时秒数 |

配置校验延迟到工具调用时：缺失配置不会导致服务器启动失败，调用相应工具时返回错误信息。

## 工具

所有路径均相对于 `WEBDAV_URL`。`read`/`write` 仅支持文本（UTF-8）；二进制文件请用 `download`/`upload`（经本地磁盘进出，不占用模型上下文）或 `copy`/`move`（远端搬运）。

| 工具 | 说明 |
|---|---|
| `list(path=".")` | 列出目录条目（name/type/size/modified），返回 JSON |
| `read(path)` | 读取文本文件；遇到二进制文件报错并提示大小 |
| `write(path, content)` | 写入文本文件（存在则覆盖）；父目录不存在时提示先 `mkdir` |
| `delete(path)` | 删除文件或目录（递归） |
| `mkdir(path)` | 创建目录 |
| `move(src, dst)` | 移动/重命名 |
| `copy(src, dst)` | 复制 |
| `stat(path)` | 查询单个路径元数据，返回 JSON |
| `download(path, local_path)` | 下载远程文件到本地路径，支持任意类型 |
| `upload(local_path, path)` | 上传本地文件到远程路径（存在则覆盖），支持任意类型 |

## Claude Code 配置示例（坚果云）

发布到 PyPI 后，使用 `uvx`（自动拉取并缓存到隔离环境）：

```json
{
  "mcpServers": {
    "webdav": {
      "command": "uvx",
      "args": ["mcp-webdav"],
      "env": {
        "WEBDAV_URL": "https://dav.jianguoyun.com/dav/",
        "WEBDAV_USERNAME": "your-account@example.com",
        "WEBDAV_PASSWORD": "your-app-password"
      }
    }
  }
}
```

发布前或本地开发，从仓库 workspace 运行：

```json
{
  "mcpServers": {
    "webdav": {
      "command": "uv",
      "args": ["run", "--package", "mcp-webdav", "mcp-webdav"],
      "env": {
        "WEBDAV_URL": "https://dav.jianguoyun.com/dav/",
        "WEBDAV_USERNAME": "your-account@example.com",
        "WEBDAV_PASSWORD": "your-app-password"
      }
    }
  }
}
```

## 开发

```bash
uv sync --all-packages
uv run --package mcp-webdav pytest mcp_servers/mcp_webdav/tests
```
