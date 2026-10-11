import json

import pytest

import webdav as mod
from webdav import _get_auth, _get_timeout, _get_url
from webdav4.client import ResourceAlreadyExists, ResourceNotFound


def test_get_url_missing_env():
    mod.WEBDAV_URL = ""
    with pytest.raises(ValueError, match="WEBDAV_URL"):
        _get_url()


def test_get_url_present():
    mod.WEBDAV_URL = "https://dav.jianguoyun.com/dav/"
    assert _get_url() == "https://dav.jianguoyun.com/dav/"


def test_get_auth_anonymous():
    mod.WEBDAV_USERNAME = ""
    mod.WEBDAV_PASSWORD = ""
    assert _get_auth() is None


def test_get_auth_pair():
    mod.WEBDAV_USERNAME = "user"
    mod.WEBDAV_PASSWORD = "pass"
    assert _get_auth() == ("user", "pass")


def test_get_auth_username_only():
    mod.WEBDAV_USERNAME = "user"
    mod.WEBDAV_PASSWORD = ""
    with pytest.raises(ValueError, match="WEBDAV_PASSWORD"):
        _get_auth()


def test_get_auth_password_only():
    mod.WEBDAV_USERNAME = ""
    mod.WEBDAV_PASSWORD = "pass"
    with pytest.raises(ValueError, match="WEBDAV_USERNAME"):
        _get_auth()


def test_get_timeout_default():
    mod.WEBDAV_TIMEOUT = ""
    assert _get_timeout() == 30.0


def test_get_timeout_valid():
    mod.WEBDAV_TIMEOUT = "10"
    assert _get_timeout() == 10.0


@pytest.mark.parametrize("value", ["abc", "0", "-5"])
def test_get_timeout_invalid(value):
    mod.WEBDAV_TIMEOUT = value
    with pytest.raises(ValueError, match="WEBDAV_TIMEOUT"):
        _get_timeout()


def test_get_client_uses_config(monkeypatch):
    mod.WEBDAV_URL = "https://dav.example.com/dav/"
    mod.WEBDAV_USERNAME = "user"
    mod.WEBDAV_PASSWORD = "pass"
    mod.WEBDAV_TIMEOUT = "10"
    captured = {}

    def fake_client(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(mod, "Client", fake_client)
    mod._get_client()
    assert captured["base_url"] == "https://dav.example.com/dav/"
    assert captured["auth"] == ("user", "pass")
    assert captured["timeout"] == 10.0


def test_get_client_anonymous(monkeypatch):
    mod.WEBDAV_URL = "https://dav.example.com/dav/"
    mod.WEBDAV_USERNAME = ""
    mod.WEBDAV_PASSWORD = ""
    mod.WEBDAV_TIMEOUT = ""
    captured = {}

    def fake_client(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(mod, "Client", fake_client)
    mod._get_client()
    assert captured["auth"] is None
    assert captured["timeout"] == 30.0


class FakeClient:
    def __init__(self, ls=None, info=None, open=None):
        self.ls = ls or (lambda path: [])
        self.info = info or (lambda path: {})
        self.open = open


def _patch_client(monkeypatch, fake):
    monkeypatch.setattr(mod, "_get_client", lambda: fake)


@pytest.mark.asyncio
async def test_list_returns_entries(monkeypatch):
    def ls(path):
        return [
            {"name": "docs", "type": "directory", "content_length": None,
             "modified": "2026-10-10T10:00:00Z"},
            {"name": "a.txt", "type": "file", "content_length": 12,
             "modified": "2026-10-11T09:30:00Z"},
        ]

    _patch_client(monkeypatch, FakeClient(ls=ls))
    result = await mod.list(path="docs")
    entries = json.loads(result)
    assert [e["name"] for e in entries] == ["docs", "a.txt"]
    assert entries[0]["type"] == "directory"
    assert entries[1]["size"] == 12


@pytest.mark.asyncio
async def test_list_defaults_to_root(monkeypatch):
    holder = {}

    def ls(path):
        holder["path"] = path
        return []

    _patch_client(monkeypatch, FakeClient(ls=ls))
    await mod.list()
    assert holder["path"] == "."


@pytest.mark.asyncio
async def test_list_path_not_found(monkeypatch):
    def ls(path):
        raise ResourceNotFound(path)

    _patch_client(monkeypatch, FakeClient(ls=ls))
    result = await mod.list(path="missing")
    assert "路径不存在" in result
    assert "missing" in result


class FakeFile:
    def __init__(self, data: bytes):
        self._data = data

    def read(self) -> bytes:
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@pytest.mark.asyncio
async def test_read_returns_text(monkeypatch):
    def open_file(path, mode="rb"):
        assert mode == "rb"
        return FakeFile("hello 世界".encode())

    _patch_client(monkeypatch, FakeClient(open=open_file))
    result = await mod.read(path="a.txt")
    assert result == "hello 世界"


@pytest.mark.asyncio
async def test_read_binary_rejected(monkeypatch):
    def open_file(path, mode="rb"):
        return FakeFile(b"\x80\x81\x82")

    _patch_client(monkeypatch, FakeClient(open=open_file))
    result = await mod.read(path="img.png")
    assert "疑似二进制文件" in result
    assert "3" in result
    assert "img.png" in result


@pytest.mark.asyncio
async def test_read_path_not_found(monkeypatch):
    def open_file(path, mode="rb"):
        raise ResourceNotFound(path)

    _patch_client(monkeypatch, FakeClient(open=open_file))
    result = await mod.read(path="missing.txt")
    assert "路径不存在" in result
    assert "missing.txt" in result


class WriteClient:
    def __init__(self, exists=True):
        self.uploaded = {}
        self.exists = lambda p: exists

    def upload_fileobj(self, file_obj, to_path, overwrite=False):
        self.uploaded[to_path] = (file_obj.read(), overwrite)


@pytest.mark.asyncio
async def test_write_creates_file(monkeypatch):
    fake = WriteClient(exists=True)
    _patch_client(monkeypatch, fake)
    result = await mod.write(path="a.txt", content="hello")
    assert fake.uploaded["a.txt"] == ("hello".encode(), True)
    assert "a.txt" in result


@pytest.mark.asyncio
async def test_write_overwrites_existing(monkeypatch):
    fake = WriteClient(exists=True)
    _patch_client(monkeypatch, fake)
    await mod.write(path="a.txt", content="new content")
    assert fake.uploaded["a.txt"][1] is True


@pytest.mark.asyncio
async def test_write_parent_missing(monkeypatch):
    fake = WriteClient(exists=False)
    _patch_client(monkeypatch, fake)
    result = await mod.write(path="nodir/a.txt", content="hello")
    assert "mkdir" in result
    assert "nodir" in result
    assert fake.uploaded == {}


class DeleteClient:
    def __init__(self, error=None):
        self.removed = []
        self._error = error

    def remove(self, path):
        if self._error:
            raise self._error(path)
        self.removed.append(path)


@pytest.mark.asyncio
async def test_delete_file(monkeypatch):
    fake = DeleteClient()
    _patch_client(monkeypatch, fake)
    result = await mod.delete(path="a.txt")
    assert fake.removed == ["a.txt"]
    assert "a.txt" in result


@pytest.mark.asyncio
async def test_delete_directory(monkeypatch):
    fake = DeleteClient()
    _patch_client(monkeypatch, fake)
    result = await mod.delete(path="docs")
    assert fake.removed == ["docs"]
    assert "docs" in result


@pytest.mark.asyncio
async def test_delete_path_not_found(monkeypatch):
    fake = DeleteClient(error=ResourceNotFound)
    _patch_client(monkeypatch, fake)
    result = await mod.delete(path="missing")
    assert "路径不存在" in result
    assert "missing" in result


class MkdirClient:
    def __init__(self, error=None):
        self.created = []
        self._error = error

    def mkdir(self, path):
        if self._error:
            raise self._error(path)
        self.created.append(path)


@pytest.mark.asyncio
async def test_mkdir_creates(monkeypatch):
    fake = MkdirClient()
    _patch_client(monkeypatch, fake)
    result = await mod.mkdir(path="photos/2026")
    assert fake.created == ["photos/2026"]
    assert "photos/2026" in result


@pytest.mark.asyncio
async def test_mkdir_already_exists(monkeypatch):
    fake = MkdirClient(error=ResourceAlreadyExists)
    _patch_client(monkeypatch, fake)
    result = await mod.mkdir(path="docs")
    assert "已存在" in result
    assert "docs" in result


class TransferClient:
    def __init__(self, error=None):
        self.transfers = []
        self._error = error

    def move(self, from_path, to_path, overwrite=False):
        self._do("move", from_path, to_path, overwrite)

    def copy(self, from_path, to_path, overwrite=False):
        self._do("copy", from_path, to_path, overwrite)

    def _do(self, method, from_path, to_path, overwrite):
        if self._error:
            raise self._error(from_path)
        self.transfers.append((method, from_path, to_path, overwrite))


@pytest.mark.asyncio
async def test_move(monkeypatch):
    fake = TransferClient()
    _patch_client(monkeypatch, fake)
    result = await mod.move(src="a.txt", dst="backup/a.txt")
    assert fake.transfers == [("move", "a.txt", "backup/a.txt", False)]
    assert "a.txt" in result
    assert "backup/a.txt" in result


@pytest.mark.asyncio
async def test_move_source_not_found(monkeypatch):
    fake = TransferClient(error=ResourceNotFound)
    _patch_client(monkeypatch, fake)
    result = await mod.move(src="missing", dst="x")
    assert "路径不存在" in result
    assert "missing" in result


@pytest.mark.asyncio
async def test_copy(monkeypatch):
    fake = TransferClient()
    _patch_client(monkeypatch, fake)
    result = await mod.copy(src="a.txt", dst="b.txt")
    assert fake.transfers == [("copy", "a.txt", "b.txt", False)]
    assert "b.txt" in result


@pytest.mark.asyncio
async def test_copy_source_not_found(monkeypatch):
    fake = TransferClient(error=ResourceNotFound)
    _patch_client(monkeypatch, fake)
    result = await mod.copy(src="missing", dst="x")
    assert "路径不存在" in result
    assert "missing" in result


@pytest.mark.asyncio
async def test_stat_returns_metadata(monkeypatch):
    def info(path):
        return {
            "name": "a.txt",
            "type": "file",
            "content_length": 12,
            "modified": "2026-10-11T09:30:00Z",
        }

    _patch_client(monkeypatch, FakeClient(info=info))
    result = await mod.stat(path="a.txt")
    data = json.loads(result)
    assert data["name"] == "a.txt"
    assert data["type"] == "file"
    assert data["size"] == 12


@pytest.mark.asyncio
async def test_stat_path_not_found(monkeypatch):
    def info(path):
        raise ResourceNotFound(path)

    _patch_client(monkeypatch, FakeClient(info=info))
    result = await mod.stat(path="missing")
    assert "路径不存在" in result
    assert "missing" in result


class DownloadClient:
    def __init__(self, error=None):
        self.downloads = []
        self._error = error

    def download_file(self, from_path, to_path):
        if self._error:
            raise self._error(from_path)
        self.downloads.append((from_path, to_path))


@pytest.mark.asyncio
async def test_download_to_local_path(monkeypatch, tmp_path):
    fake = DownloadClient()
    _patch_client(monkeypatch, fake)
    local = tmp_path / "img.png"
    result = await mod.download(path="img.png", local_path=str(local))
    assert fake.downloads == [("img.png", str(local))]
    assert "img.png" in result


@pytest.mark.asyncio
async def test_download_remote_not_found(monkeypatch, tmp_path):
    fake = DownloadClient(error=ResourceNotFound)
    _patch_client(monkeypatch, fake)
    result = await mod.download(
        path="missing", local_path=str(tmp_path / "x")
    )
    assert "路径不存在" in result
    assert "missing" in result
    assert fake.downloads == []


@pytest.mark.asyncio
async def test_download_local_dir_missing(monkeypatch):
    fake = DownloadClient()
    _patch_client(monkeypatch, fake)
    result = await mod.download(
        path="img.png", local_path="/nonexistent-dir-xyz/img.png"
    )
    assert "本地" in result
    assert fake.downloads == []


class UploadClient:
    def __init__(self, exists=True):
        self.uploads = []
        self.exists = lambda p: exists

    def upload_file(self, from_path, to_path, overwrite=False):
        self.uploads.append((from_path, to_path, overwrite))


@pytest.mark.asyncio
async def test_upload_from_local_file(monkeypatch, tmp_path):
    local = tmp_path / "a.zip"
    local.write_bytes(b"\x80\x81zip-data")
    fake = UploadClient()
    _patch_client(monkeypatch, fake)
    result = await mod.upload(local_path=str(local), path="backup/a.zip")
    assert fake.uploads == [(str(local), "backup/a.zip", True)]
    assert "backup/a.zip" in result


@pytest.mark.asyncio
async def test_upload_local_file_missing(monkeypatch, tmp_path):
    fake = UploadClient()
    _patch_client(monkeypatch, fake)
    result = await mod.upload(
        local_path=str(tmp_path / "nope.zip"), path="backup/a.zip"
    )
    assert "本地文件不存在" in result
    assert fake.uploads == []


@pytest.mark.asyncio
async def test_upload_remote_parent_missing(monkeypatch, tmp_path):
    local = tmp_path / "a.zip"
    local.write_bytes(b"data")
    fake = UploadClient(exists=False)
    _patch_client(monkeypatch, fake)
    result = await mod.upload(local_path=str(local), path="nodir/a.zip")
    assert "mkdir" in result
    assert "nodir" in result
    assert fake.uploads == []
