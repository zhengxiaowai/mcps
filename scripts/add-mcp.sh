#!/bin/bash
set -euo pipefail

NAME="${1:?Usage: $0 <name>}"

if [[ ! "${NAME}" =~ ^[a-z][a-z0-9_]*$ ]]; then
    echo "Error: name must match ^[a-z][a-z0-9_]*$" >&2
    exit 1
fi

PACKAGE="mcp-${NAME}"
MODULE="mcp_${NAME}"
DIR="mcp_servers/${MODULE}"

if [[ -d "${DIR}" ]]; then
    echo "Error: ${DIR} already exists" >&2
    exit 1
fi

mkdir -p "${DIR}/${MODULE}"
mkdir -p "${DIR}/tests"

cat > "${DIR}/pyproject.toml" << TOML
[project]
name = "${PACKAGE}"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["fastmcp>=2.0"]

[project.scripts]
${PACKAGE} = "${MODULE}.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["${MODULE}"]
TOML

cat > "${DIR}/${MODULE}/__init__.py" << PYTHON
PYTHON

cat > "${DIR}/${MODULE}/server.py" << PYTHON
from fastmcp import FastMCP

server = FastMCP("${PACKAGE}", version="0.1.0")

# Add your tools here


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
PYTHON

echo "[OK] MCP '${PACKAGE}' created at ${DIR}/"
echo "     uv pip install -e ${DIR} && uv run ${PACKAGE}"
