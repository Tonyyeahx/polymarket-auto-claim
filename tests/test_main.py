import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_run_once_calls_redeem_all():
    """run_once should call redeem_all_positions with settings values."""
    settings = MagicMock()
    settings.private_key.get_secret_value.return_value = "0x" + "a" * 64
    settings.wallet_address = "0x" + "b" * 40
    settings.polygon_rpc_url = "https://polygon-rpc.com"

    with patch("main.get_settings", return_value=settings), \
         patch("main.redeem_all_positions", new_callable=AsyncMock) as mock_redeem:
        mock_redeem.return_value = {"redeemed": 1, "failed": 0, "total_value": 5.0}
        import main
        await main.run_once()
        mock_redeem.assert_called_once_with(
            settings.wallet_address,
            settings.private_key.get_secret_value(),
            settings.polygon_rpc_url,
        )


@pytest.mark.asyncio
async def test_run_once_handles_exception_gracefully():
    """run_once should catch exceptions and log them without crashing."""
    settings = MagicMock()
    settings.private_key.get_secret_value.return_value = "0x" + "a" * 64
    settings.wallet_address = "0x" + "b" * 40
    settings.polygon_rpc_url = "https://polygon-rpc.com"

    with patch("main.get_settings", return_value=settings), \
         patch("main.redeem_all_positions", new_callable=AsyncMock) as mock_redeem:
        mock_redeem.side_effect = RuntimeError("network failure")
        import main
        # Should not raise
        await main.run_once()
