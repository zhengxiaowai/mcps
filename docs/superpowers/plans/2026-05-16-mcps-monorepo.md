# MCPS Monorepo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold a uv workspace monorepo with a shared `core` package and an example `hello` MCP server.

**Architecture:** uv workspace with `packages/*` members. `mcps-core` wraps FastMCP factory + serve. `mcps-hello` depends on core and defines one tool. One script to generate new MCPs.

**Tech Stack:** Python 3.12, uv, FastMCP, stdio transport

**Spec:** `docs/superpowers/specs/2026-05-16-mcps-monorepo-design.md`

---

### Task 1: Root pyproject.toml

**Files:**
- Create: `pyproject.toml`

- [ ] **Step 1: Write root pyproject.toml**

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

- [ ] **Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add root workspace config"
```

---

### Task 2: Core package

**Files:**
- Create: `packages/core/pyproject.toml`
- Create: `packages/core/src/mcps_core/__init__.py`
- Create: `packages/core/src/mcps_core/server.py`
- Create: `packages/core/src/mcps_core/config.py`

- [ ] **Step 1: Write core pyproject.toml**

```toml
[project]
name = "mcps-core"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["fastmcp>=2.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Write core package __init__.py**

```python
from mcps_core.server import create_server, serve

__all__ = ["create_server", "serve"]
```

- [ ] **Step 3: Write server.py**

```python
from fastmcp import FastMCP


def create_server(name: str) -> FastMCP:
    """Create a FastMCP server instance."""
    return FastMCP(name)


def serve(server: FastMCP) -> None:
    """Run the server with stdio transport."""
    server.run()
```

- [ ] **Step 4: Write config.py**

```python
import logging
import os


def configure_logging(level: int | None = None) -> None:
    """Set up logging for MCP servers."""
    if level is None:
        level = getattr(logging, os.environ.get("LOG_LEVEL", "INFO"))
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
```

- [ ] **Step 5: Commit**

```bash
git add packages/core/
git commit -m "feat: add mcps-core package"
```

---

### Task 3: Core tests

**Files:**
- Create: `packages/core/tests/__init__.py`
- Create: `packages/core/tests/test_server.py`

- [ ] **Step 1: Write test file**

```python
from fastmcp import FastMCP
from mcps_core import create_server, serve


def test_create_server_returns_fastmcp_instance():
    server = create_server("test")
    assert isinstance(server, FastMCP)


def test_create_server_sets_name():
    server = create_server("test-server")
    assert server.name == "test-server"
```

- [ ] **Step 2: Run tests to verify they fail (core not yet installed)**

Run: `uv run pytest packages/core/tests/ -v`
Expected: Import error — mcps_core not found. Install with `uv sync` in next step.

- [ ] **Step 3: Sync workspace and run tests**

```bash
uv sync
uv run pytest packages/core/tests/ -v
```

Expected: 2 passed

- [ ] **Step 4: Commit**

```bash
git add packages/core/tests/
git commit -m "test: add core server tests"
```

---

### Task 4: Hello MCP package

**Files:**
- Create: `packages/hello/pyproject.toml`
- Create: `packages/hello/src/mcps_hello/__init__.py`
- Create: `packages/hello/src/mcps_hello/server.py`

- [ ] **Step 1: Write hello pyproject.toml**

```toml
[project]
name = "mcps-hello"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["mcps-core"]

[project.scripts]
mcps-hello = "mcps_hello.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Write hello __init__.py (empty)**

```python
```

- [ ] **Step 3: Write hello server.py**

```python
from mcps_core import create_server, serve

server = create_server("hello")


@server.tool
def greet(name: str = "world") -> str:
    """Say hello."""
    return f"Hello, {name}!"


def main() -> None:
    serve(server)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run uv sync to install hello and its dependencies**

```bash
uv sync
```

Expected: mcps-hello installed in workspace venv

- [ ] **Step 5: Commit**

```bash
git add packages/hello/
git commit -m "feat: add mcps-hello example MCP"
```

---

### Task 5: Hello tests

**Files:**
- Create: `packages/hello/tests/__init__.py`
- Create: `packages/hello/tests/test_server.py`

- [ ] **Step 1: Write test file**

```python
from mcps_hello.server import greet


def test_greet_with_name():
    result = greet("Alice")
    assert result == "Hello, Alice!"


def test_greet_default():
    result = greet()
    assert result == "Hello, world!"
```

- [ ] **Step 2: Run tests**

```bash
uv run pytest packages/hello/tests/ -v
```

Expected: 2 passed

- [ ] **Step 3: Commit**

```bash
git add packages/hello/tests/
git commit -m "test: add hello server tests"
```

---

### Task 6: Scaffolding script

**Files:**
- Create: `scripts/add-mcp.sh`

- [ ] **Step 1: Write add-mcp.sh**

```bash
#!/bin/bash
set -euo pipefail

NAME="${1:?Usage: $0 <name>}"
PACKAGE="mcps-${NAME}"
MODULE="mcps_${NAME}"
DIR="packages/${NAME}"

if [[ -d "${DIR}" ]]; then
    echo "Error: ${DIR} already exists"
    exit 1
fi

mkdir -p "${DIR}/src/${MODULE}"
mkdir -p "${DIR}/tests"

cat > "${DIR}/pyproject.toml" << TOML
[project]
name = "${PACKAGE}"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["mcps-core"]

[project.scripts]
${PACKAGE} = "${MODULE}.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
TOML

cat > "${DIR}/src/${MODULE}/__init__.py" << PYTHON
PYTHON

cat > "${DIR}/src/${MODULE}/server.py" << PYTHON
from mcps_core import create_server, serve

server = create_server("${NAME}")

# Add your tools here


def main() -> None:
    serve(server)


if __name__ == "__main__":
    main()
PYTHON

touch "${DIR}/tests/__init__.py"

echo "[OK] MCP '${NAME}' created at ${DIR}/"
echo "     uv sync && uv run ${PACKAGE}"
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x scripts/add-mcp.sh
```

- [ ] **Step 3: Commit**

```bash
git add scripts/
git commit -m "feat: add MCP scaffolding script"
```

---

### Task 7: Full verification

- [ ] **Step 1: Run full test suite**

```bash
uv run pytest packages/ -v
```

Expected: All tests pass (2 core + 2 hello = 4)

- [ ] **Step 2: Verify hello MCP is importable and configured**

```bash
uv run python -c "from mcps_hello.server import server; print(server.name)"
```

Expected: `hello`

- [ ] **Step 3: Verify scaffolding script generates correct files**

```bash
./scripts/add-mcp.sh demo
ls packages/demo/src/mcps_demo/server.py
```

Expected: `packages/demo/src/mcps_demo/server.py`

- [ ] **Step 4: Clean up demo**

```bash
rm -rf packages/demo
```

- [ ] **Step 5: Confirm working tree is clean**

```bash
git status
```

Expected: working tree clean
