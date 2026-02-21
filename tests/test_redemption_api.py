import pytest
import respx
import httpx
from redemption import get_redeemable_positions

WALLET = "0x" + "a" * 40


@pytest.mark.asyncio
async def test_returns_only_redeemable_positions():
    positions = [
        {"conditionId": "0x01", "redeemable": True,  "size": "10.0", "outcome": "YES"},
        {"conditionId": "0x02", "redeemable": False, "size": "5.0",  "outcome": "NO"},
        {"conditionId": "0x03", "redeemable": True,  "size": "0.0",  "outcome": "YES"},
        {"conditionId": "0x04", "redeemable": True,  "size": "3.0",  "outcome": "NO"},
    ]
    url = f"https://data-api.polymarket.com/positions?user={WALLET}"
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(200, json=positions))
        result = await get_redeemable_positions(WALLET)

    # Only positions with redeemable=True AND size > 0
    assert len(result) == 2
    assert result[0]["conditionId"] == "0x01"
    assert result[1]["conditionId"] == "0x04"


@pytest.mark.asyncio
async def test_returns_empty_when_no_redeemable():
    url = f"https://data-api.polymarket.com/positions?user={WALLET}"
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(200, json=[]))
        result = await get_redeemable_positions(WALLET)
    assert result == []


@pytest.mark.asyncio
async def test_raises_on_http_error():
    url = f"https://data-api.polymarket.com/positions?user={WALLET}"
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(500))
        with pytest.raises(httpx.HTTPStatusError):
            await get_redeemable_positions(WALLET)
