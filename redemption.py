"""Auto-redemption for Polymarket won positions."""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Any

import httpx

from web3 import Web3

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

# ---------------------------------------------------------------------------
# On-chain redemption
# ---------------------------------------------------------------------------


def redeem_position_sync(
    position: dict[str, Any],
    private_key: str,
    rpc_url: str,
) -> bool:
    """Submit a redeemPositions transaction. Returns True on success."""
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
    if not w3.is_connected(show_traceback=True):
        log.error("rpc_not_connected rpc=%s", rpc_url)
        return False

    account = w3.eth.account.from_key(private_key)
    wallet = account.address

    try:
        condition_id: str = position.get("conditionId", "")
        if not condition_id:
            log.warning("skipping_position missing_condition_id")
            return False
        neg_risk: bool = bool(position.get("negRisk", False))
        outcome: str = position.get("outcome", "")
        index_sets = _outcome_to_index_sets(outcome)
        condition_bytes = _condition_id_to_bytes32(condition_id)

        nonce = w3.eth.get_transaction_count(wallet, "pending")
        gas_price = int(w3.eth.gas_price * 1.1)

        if neg_risk:
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(NEG_RISK_ADAPTER_ADDRESS),
                abi=NEG_RISK_REDEEM_ABI,
            )
            tx = contract.functions.redeemPositions(
                condition_bytes,
                index_sets,
            ).build_transaction(
                {"from": wallet, "nonce": nonce, "gas": 200_000, "gasPrice": gas_price, "chainId": 137}
            )
        else:
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(CTF_ADDRESS),
                abi=CTF_REDEEM_ABI,
            )
            tx = contract.functions.redeemPositions(
                Web3.to_checksum_address(USDC_ADDRESS),
                b"\x00" * 32,
                condition_bytes,
                index_sets,
            ).build_transaction(
                {"from": wallet, "nonce": nonce, "gas": 200_000, "gasPrice": gas_price, "chainId": 137}
            )

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        success = receipt.status == 1
        if success:
            log.info("redeemed condition=%s tx=%s", condition_id, tx_hash.hex())
        else:
            log.warning("reverted condition=%s tx=%s", condition_id, tx_hash.hex())
        return success

    except Exception as exc:
        log.error("redemption_error condition=%s error=%s", position.get("conditionId", ""), exc)
        return False


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


async def redeem_all_positions(
    wallet_address: str,
    private_key: str,
    rpc_url: str,
) -> dict[str, Any]:
    """Fetch redeemable positions and redeem them all. Returns a summary dict."""
    positions = await get_redeemable_positions(wallet_address)

    if not positions:
        log.info("no_redeemable_positions")
        return {"skipped": True, "reason": "no redeemable positions"}

    redeemed = 0
    failed = 0
    total_value = 0.0

    for position in positions:
        ok = await asyncio.to_thread(redeem_position_sync, position, private_key, rpc_url)
        if ok:
            redeemed += 1
            total_value += float(position.get("currentValue", 0))
        else:
            failed += 1

    log.info("cycle_done redeemed=%d failed=%d value=%.2f", redeemed, failed, total_value)
    return {"redeemed": redeemed, "failed": failed, "total_value": total_value}
