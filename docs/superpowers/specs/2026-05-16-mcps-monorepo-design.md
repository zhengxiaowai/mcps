# MCPS Monorepo 设计

## 概述

基于 FastMCP 的 Python monorepo，每个 `packages/<name>/` 目录是一个独立的 MCP server。使用 uv workspace 管理多包依赖，`core` 包封装共享逻辑。

## 技术选型

- Python 3.12
- uv (包管理 + workspace)
- FastMCP (MCP server 框架)
- stdio transport

## 目录结构

```
mcps/
├── pyproject.toml            # uv workspace 根配置
├── uv.lock                   # 全局锁文件
├── README.md
├── .python-version           # 3.12
├── packages/
│   ├── core/
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   └── mcps_core/
│   │   │       ├── __init__.py
│   │   │       ├── server.py       # FastMCP 工厂函数
│   │   │       └── config.py       # 公共配置
│   │   └── tests/
│   └── hello/
│       ├── pyproject.toml
│       ├── src/
│       │   └── mcps_hello/
│       │       ├── __init__.py
│       │       └── server.py       # hello world MCP
│       └── tests/
└── scripts/
    └── add-mcp.sh                 # 脚手架脚本
```

## 命名约定

- PyPI 包名: `mcps-<name>` (kebab)
- Python 模块名: `mcps_<name>` (snake)
- 目录名: `packages/<name>/`

## Core 包

### server.py

- `create_server(name, version=None)` — 创建 FastMCP 实例，统一 stdio transport 配置
- `serve(server)` — 启动 server + 信号处理 + 优雅关闭

### config.py

- 统一日志配置
- 环境变量读取

### 依赖

- `fastmcp`（唯一外部依赖）

## Hello 示例

`packages/hello/` 提供最小 MCP server：

- 单一 tool `greet(name="world")` 返回 `"Hello, {name}!"`
- 入口点 `mcps-hello = "mcps_hello.server:serve"`
- 通过 `uv run mcps-hello` 启动

## 开发工作流

### 添加新 MCP

```bash
./scripts/add-mcp.sh <name>
```

生成 `packages/<name>/` 含 pyproject.toml、src/mcps_<name>/server.py、tests/。

### 运行

```bash
uv run mcps-<name>          # 启动指定 MCP
uv run pytest               # 运行所有测试
```

## Root pyproject.toml

```toml
[project]
name = "mcps"
version = "0.1.0"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["packages/*"]

[tool.uv]
package = false
```

[project.scripts] 留在各子包中定义。
