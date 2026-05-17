import os

import httpx
from fastmcp import FastMCP
from loguru import logger

server = FastMCP("mcp-serverchan-turbo", version="0.1.0")

SCT_API_URL = os.environ.get("SCT_API_URL", "")


def _get_api_url() -> str:
    if not SCT_API_URL:
        raise ValueError("SCT_API_URL environment variable is required")
    return SCT_API_URL


@server.tool
async def send(title: str, desp: str = "", short: str = "") -> str:
    """Send a push notification via ServerChan Turbo.

    Args:
        title: Notification title (required, max 32 chars)
        desp: Notification body, supports Markdown (optional, max 32KB)
        short: Short description for card preview (optional, max 64 chars)
    """
    url = _get_api_url()
    payload: dict[str, str] = {"title": title}
    if desp:
        payload["desp"] = desp
    if short:
        payload["short"] = short

    headers = {"Content-Type": "application/json;charset=utf-8"}

    logger.info("sending notification: title={}", title)
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        logger.info("notification sent: status={}", resp.status_code)
        return resp.text


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
