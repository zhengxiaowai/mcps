import json
import os

import pytest

from serverchan_turbo import _get_api_url, send


def test_get_api_url_missing_env():
    os.environ.pop("SCT_API_URL", None)
    import serverchan_turbo as mod

    mod.SCT_API_URL = ""
    with pytest.raises(ValueError, match="SCT_API_URL"):
        _get_api_url()


def test_get_api_url_present():
    import serverchan_turbo as mod

    mod.SCT_API_URL = "https://sctapi.ftqq.com/testkey.send"
    assert _get_api_url() == "https://sctapi.ftqq.com/testkey.send"


@pytest.mark.asyncio
async def test_send_calls_api(httpx_mock):
    import serverchan_turbo as mod

    mod.SCT_API_URL = "https://sctapi.ftqq.com/testkey.send"
    httpx_mock.add_response(
        url="https://sctapi.ftqq.com/testkey.send", text='{"code":0}'
    )
    result = await send(title="hello", desp="world")
    assert '"code":0' in result


@pytest.mark.asyncio
async def test_send_json_content_type(httpx_mock):
    import serverchan_turbo as mod

    mod.SCT_API_URL = "https://sctapi.ftqq.com/testkey.send"
    httpx_mock.add_response(
        url="https://sctapi.ftqq.com/testkey.send", text='{"code":0}'
    )
    await send(title="hello")
    request = httpx_mock.get_requests()[-1]
    assert request.headers["content-type"] == "application/json;charset=utf-8"


@pytest.mark.asyncio
async def test_send_optional_params(httpx_mock):
    import serverchan_turbo as mod

    mod.SCT_API_URL = "https://sctapi.ftqq.com/testkey.send"
    httpx_mock.add_response(
        url="https://sctapi.ftqq.com/testkey.send", text='{"code":0}'
    )
    result = await send(title="alert", short="brief")
    assert '"code":0' in result
    request = httpx_mock.get_requests()[-1]
    body = json.loads(request.content)
    assert body["title"] == "alert"
    assert body["short"] == "brief"
    assert "desp" not in body
