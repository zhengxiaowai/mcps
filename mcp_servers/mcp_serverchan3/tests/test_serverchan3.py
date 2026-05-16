import os

import pytest

from serverchan3 import _get_api_url, send


def test_get_api_url_missing_env():
    os.environ.pop("SC3_API_URL", None)
    import serverchan3 as mod
    mod.SC3_API_URL = ""
    with pytest.raises(ValueError, match="SC3_API_URL"):
        _get_api_url()


def test_get_api_url_present():
    import serverchan3 as mod
    mod.SC3_API_URL = "https://1.push.ft07.com/send/abc.send"
    assert _get_api_url() == "https://1.push.ft07.com/send/abc.send"


@pytest.mark.asyncio
async def test_send_calls_api(httpx_mock):
    import serverchan3 as mod
    mod.SC3_API_URL = "https://1.push.ft07.com/send/abc.send"
    httpx_mock.add_response(url="https://1.push.ft07.com/send/abc.send", text='{"code":0}')
    result = await send(title="hello", desp="world")
    assert '"code":0' in result


@pytest.mark.asyncio
async def test_send_optional_params(httpx_mock):
    import serverchan3 as mod
    mod.SC3_API_URL = "https://1.push.ft07.com/send/abc.send"
    httpx_mock.add_response(url="https://1.push.ft07.com/send/abc.send", text='{"code":0}')
    result = await send(title="alert", tags="server|prod", short="brief")
    assert '"code":0' in result
    request = httpx_mock.get_requests()[-1]
    import json
    body = json.loads(request.content)
    assert body["title"] == "alert"
    assert body["tags"] == "server|prod"
    assert body["short"] == "brief"
    assert "desp" not in body
