# mcp-serverchan-turbo

ServerChan Turbo push notification MCP server.

## Install

```bash
uvx mcp-serverchan-turbo
```

## Configuration

Set the `SCT_API_URL` environment variable to your ServerChan Turbo push URL:

```
SCT_API_URL=https://sctapi.ftqq.com/<your-key>.send
```

## Tools

### send

Send a push notification via ServerChan Turbo.

| Parameter | Required | Description |
|-----------|----------|-------------|
| title     | Yes      | Notification title (max 32 chars) |
| desp      | No       | Notification body, supports Markdown (max 32KB) |
| short     | No       | Short description for card preview (max 64 chars) |

## Claude Desktop Integration

```json
{
  "mcpServers": {
    "serverchan-turbo": {
      "command": "uvx",
      "args": ["mcp-serverchan-turbo"],
      "env": {
        "SCT_API_URL": "https://sctapi.ftqq.com/<your-key>.send"
      }
    }
  }
}
```
