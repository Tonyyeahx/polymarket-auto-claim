"""Auto-redemption for Polymarket won positions."""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Contract addresses — Polygon mainnet
# ---------------------------------------------------------------------------

CTF_ADDRESS = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
NEG_RISK_ADAPTER_ADDRESS = "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296"

CTF_REDEEM_ABI = [
    {
        "inputs": [
            {"name": "collateralToken", "type": "address"},
            {"name": "parentCollectionId", "type": "bytes32"},
            {"name": "conditionId", "type": "bytes32"},
            {"name": "indexSets", "type": "uint256[]"},
        ],
        "name": "redeemPositions",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

NEG_RISK_REDEEM_ABI = [
    {
        "inputs": [
            {"name": "conditionId", "type": "bytes32"},
            {"name": "indexSets", "type": "uint256[]"},
        ],
        "name": "redeemPositions",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

POSITIONS_API_URL = "https://data-api.polymarket.com/positions"

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _outcome_to_index_sets(outcome: str) -> list[int]:
    """Map outcome string to CTF index sets."""
    if outcome.upper() == "YES":
        return [1]
    if outcome.upper() == "NO":
        return [2]
    return [1, 2]


def _condition_id_to_bytes32(condition_id: str) -> bytes:
    """Convert a hex condition ID (with or without 0x prefix) to 32 bytes."""
    hex_str = condition_id.removeprefix("0x")
    return bytes.fromhex(hex_str.zfill(64))

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


async def get_redeemable_positions(wallet_address: str) -> list[dict[str, Any]]:
    """Fetch positions from Polymarket data API and return redeemable ones."""
    url = f"{POSITIONS_API_URL}?user={wallet_address}"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()
        positions: list[dict[str, Any]] = response.json()

    return [
        p
        for p in positions
        if p.get("redeemable") is True and float(p.get("size", 0)) > 0
    ]
