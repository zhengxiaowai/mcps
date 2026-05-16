from fastmcp import FastMCP

server = FastMCP("mcp-hello", version="0.1.0")


@server.tool
def greet(name: str = "world") -> str:
    """Say hello."""
    return f"Hello, {name}!"


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
