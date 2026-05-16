import os

import httpx
from fastmcp import FastMCP
from loguru import logger

server = FastMCP("mcp-serverchan3", version="0.1.0")

SC3_API_URL = os.environ.get("SC3_API_URL", "")


def _get_api_url() -> str:
    if not SC3_API_URL:
        raise ValueError("SC3_API_URL environment variable is required")
    return SC3_API_URL


@server.tool
async def send(title: str, desp: str = "", tags: str = "", short: str = "") -> str:
    """Send a push notification via ServerChan3.

    Args:
        title: Notification title (required)
        desp: Notification body, supports Markdown (optional)
        tags: Pipe-separated tags, e.g. "alert|server" (optional)
        short: Short description for card preview (optional)
    """
    url = _get_api_url()
    payload: dict[str, str] = {"title": title}
    if desp:
        payload["desp"] = desp
    if tags:
        payload["tags"] = tags
    if short:
        payload["short"] = short

    logger.info("sending notification: title={}", title)
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("notification sent: status={}", resp.status_code)
        return resp.text


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
