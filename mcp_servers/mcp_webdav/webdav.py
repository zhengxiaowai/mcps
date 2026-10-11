import asyncio
import io
import json
import os
import posixpath

from fastmcp import FastMCP
from loguru import logger
from webdav4.client import Client, ResourceAlreadyExists, ResourceNotFound

server = FastMCP("mcp-webdav", version="0.1.0")

WEBDAV_URL = os.environ.get("WEBDAV_URL", "")
WEBDAV_USERNAME = os.environ.get("WEBDAV_USERNAME", "")
WEBDAV_PASSWORD = os.environ.get("WEBDAV_PASSWORD", "")
WEBDAV_TIMEOUT = os.environ.get("WEBDAV_TIMEOUT", "")

DEFAULT_TIMEOUT = 30.0


def _get_url() -> str:
    if not WEBDAV_URL:
        raise ValueError("WEBDAV_URL environment variable is required")
    return WEBDAV_URL


def _get_auth() -> tuple[str, str] | None:
    if bool(WEBDAV_USERNAME) != bool(WEBDAV_PASSWORD):
        raise ValueError(
            "WEBDAV_USERNAME and WEBDAV_PASSWORD must be set together"
        )
    if not WEBDAV_USERNAME:
        return None
    return (WEBDAV_USERNAME, WEBDAV_PASSWORD)


def _get_timeout() -> float:
    if not WEBDAV_TIMEOUT:
        return DEFAULT_TIMEOUT
    try:
        timeout = float(WEBDAV_TIMEOUT)
    except ValueError:
        raise ValueError(f"invalid WEBDAV_TIMEOUT value: {WEBDAV_TIMEOUT!r}")
    if timeout <= 0:
        raise ValueError(
            f"WEBDAV_TIMEOUT must be positive, got {WEBDAV_TIMEOUT!r}"
        )
    return timeout


def _get_client() -> Client:
    return Client(
        base_url=_get_url(),
        auth=_get_auth(),
        timeout=_get_timeout(),
    )


def _not_found(path: str) -> str:
    return f"路径不存在: {path}"


def _entry_summary(entry: dict) -> dict:
    return {
        "name": entry.get("name"),
        "type": entry.get("type"),
        "size": entry.get("content_length"),
        "modified": entry.get("modified"),
    }


@server.tool
async def list(path: str = ".") -> str:
    """List directory entries on the WebDAV server.

    Args:
        path: Directory path relative to WEBDAV_URL (default: root)
    """
    client = _get_client()
    try:
        entries = await asyncio.to_thread(client.ls, path)
    except ResourceNotFound:
        return _not_found(path)
    result = [_entry_summary(entry) for entry in entries]
    logger.info("listed directory: path={} entries={}", path, len(result))
    return json.dumps(result, ensure_ascii=False, default=str)


@server.tool
async def read(path: str) -> str:
    """Read a text file (UTF-8) from the WebDAV server.

    Args:
        path: File path relative to WEBDAV_URL
    """
    client = _get_client()
    try:
        with client.open(path, "rb") as f:
            data = await asyncio.to_thread(f.read)
    except ResourceNotFound:
        return _not_found(path)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return (
            f"疑似二进制文件: {path}（大小 {len(data)} 字节）。"
            "read 仅支持文本文件；如需搬运该文件，请使用 copy/move 工具。"
        )


@server.tool
async def write(path: str, content: str) -> str:
    """Write text content to a file (created or overwritten).

    Args:
        path: File path relative to WEBDAV_URL
        content: Text content to write (UTF-8)
    """
    client = _get_client()
    parent = posixpath.dirname(path.rstrip("/"))
    if parent and parent != ".":
        exists = await asyncio.to_thread(client.exists, parent)
        if not exists:
            return f"写入失败: 父目录不存在: {parent}，请先调用 mkdir 创建"
    data = content.encode("utf-8")
    await asyncio.to_thread(client.upload_fileobj, io.BytesIO(data), path, True)
    logger.info("written file: path={} bytes={}", path, len(data))
    return f"已写入: {path}"


@server.tool
async def delete(path: str) -> str:
    """Delete a file or directory (recursively) on the WebDAV server.

    Args:
        path: File or directory path relative to WEBDAV_URL
    """
    client = _get_client()
    try:
        await asyncio.to_thread(client.remove, path)
    except ResourceNotFound:
        return _not_found(path)
    logger.info("deleted: path={}", path)
    return f"已删除: {path}"


@server.tool
async def mkdir(path: str) -> str:
    """Create a directory on the WebDAV server.

    Args:
        path: Directory path relative to WEBDAV_URL
    """
    client = _get_client()
    try:
        await asyncio.to_thread(client.mkdir, path)
    except ResourceAlreadyExists:
        return f"目录已存在: {path}"
    logger.info("created directory: path={}", path)
    return f"已创建目录: {path}"


async def _transfer(method: str, src: str, dst: str, verb_cn: str, verb_en: str) -> str:
    """Run a move or copy against the client and build the result message.

    Args:
        method: Client method to call ("move" or "copy")
        src: Source path relative to WEBDAV_URL
        dst: Destination path relative to WEBDAV_URL
        verb_cn: Chinese verb for the success message
        verb_en: English verb for the log entry
    """
    client = _get_client()
    try:
        await asyncio.to_thread(getattr(client, method), src, dst)
    except ResourceNotFound:
        return _not_found(src)
    logger.info("{}: src={} dst={}", verb_en, src, dst)
    return f"已{verb_cn}: {src} -> {dst}"


@server.tool
async def move(src: str, dst: str) -> str:
    """Move (rename) a file or directory on the WebDAV server.

    Args:
        src: Source path relative to WEBDAV_URL
        dst: Destination path relative to WEBDAV_URL
    """
    return await _transfer("move", src, dst, "移动", "moved")


@server.tool
async def copy(src: str, dst: str) -> str:
    """Copy a file or directory on the WebDAV server.

    Args:
        src: Source path relative to WEBDAV_URL
        dst: Destination path relative to WEBDAV_URL
    """
    return await _transfer("copy", src, dst, "复制", "copied")


@server.tool
async def stat(path: str) -> str:
    """Get metadata (name, type, size, modified) of a path.

    Args:
        path: File or directory path relative to WEBDAV_URL
    """
    client = _get_client()
    try:
        info = await asyncio.to_thread(client.info, path)
    except ResourceNotFound:
        return _not_found(path)
    return json.dumps(_entry_summary(info), ensure_ascii=False, default=str)


@server.tool
async def download(path: str, local_path: str) -> str:
    """Download a remote file to a local path (binary-safe, bypasses the model context).

    Args:
        path: Remote file path relative to WEBDAV_URL
        local_path: Local file path to write to
    """
    client = _get_client()
    parent = os.path.dirname(local_path)
    if parent and not os.path.isdir(parent):
        return f"下载失败: 本地目录不存在: {parent}"
    try:
        await asyncio.to_thread(client.download_file, path, local_path)
    except ResourceNotFound:
        return _not_found(path)
    logger.info("downloaded: path={} local_path={}", path, local_path)
    return f"已下载: {path} -> {local_path}"


@server.tool
async def upload(local_path: str, path: str) -> str:
    """Upload a local file to a remote path (binary-safe, bypasses the model context).

    Args:
        local_path: Local file path to read from
        path: Remote file path relative to WEBDAV_URL (overwritten if exists)
    """
    client = _get_client()
    if not os.path.isfile(local_path):
        return f"上传失败: 本地文件不存在: {local_path}"
    parent = posixpath.dirname(path.rstrip("/"))
    if parent and parent != ".":
        exists = await asyncio.to_thread(client.exists, parent)
        if not exists:
            return f"上传失败: 父目录不存在: {parent}，请先调用 mkdir 创建"
    await asyncio.to_thread(client.upload_file, local_path, path, True)
    logger.info("uploaded: local_path={} path={}", local_path, path)
    return f"已上传: {local_path} -> {path}"


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
