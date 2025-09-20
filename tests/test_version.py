import pytest
from httpx import AsyncClient, ASGITransport
from avm_platform.api.main import app
from avm_platform.version import __version__

@pytest.mark.asyncio
async def test_version():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/version")
    assert r.status_code == 200
    assert r.json() == {"version": __version__}
