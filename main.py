"""Entry point — polls Polymarket every POLL_INTERVAL seconds and redeems won positions."""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from config import get_settings
from redemption import redeem_all_positions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

_shutdown = asyncio.Event()


def _handle_signal(sig: signal.Signals) -> None:
    log.info("shutdown_requested signal=%s", sig.name)
    _shutdown.set()


async def run_once() -> None:
    """Run a single redemption cycle."""
    settings = get_settings()
    try:
        result = await redeem_all_positions(
            settings.wallet_address,
            settings.private_key.get_secret_value(),
            settings.polygon_rpc_url,
        )
        log.info("cycle_result result=%s", result)
    except Exception as exc:
        log.error("cycle_error error=%s", exc)


async def main() -> None:
    settings = get_settings()
    interval = settings.poll_interval

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: _handle_signal(s))

    log.info(
        "starting wallet=%s interval=%ds",
        settings.wallet_address,
        interval,
    )

    while not _shutdown.is_set():
        await run_once()
        try:
            await asyncio.wait_for(_shutdown.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass  # normal — timeout means next cycle

    log.info("shutdown_complete")


if __name__ == "__main__":
    asyncio.run(main())
