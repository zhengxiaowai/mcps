# mcp-serverchan3

ServerChan3 push notification MCP server.

## Usage

```bash
uvx mcp-serverchan3
```

Set environment variable:

```bash
export SC3_API_URL="https://<uid>.push.ft07.com/send/<sendkey>.send"
```

## Tools

- `send(title, desp="", tags="", short="")` — Send a push notification

## Claude Desktop Config

```json
{
  "mcpServers": {
    "serverchan3": {
      "command": "uvx",
      "args": ["mcp-serverchan3"],
      "env": {
        "SC3_API_URL": "https://<uid>.push.ft07.com/send/<sendkey>.send"
      }
    }
  }
}
```
