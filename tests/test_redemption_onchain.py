from unittest.mock import MagicMock, patch
from redemption import redeem_position_sync

PRIVATE_KEY = "0x" + "a" * 64
RPC_URL = "https://polygon-rpc.com"


def _make_position(neg_risk: bool = False, outcome: str = "YES") -> dict:
    return {
        "conditionId": "0x" + "c" * 64,
        "negRisk": neg_risk,
        "outcome": outcome,
        "currentValue": 12.5,
    }


def _mock_web3(connected: bool = True, tx_status: int = 1):
    """Build a minimal mock Web3 chain."""
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = connected
    mock_w3.eth.get_transaction_count.return_value = 0
    mock_w3.eth.gas_price = 30_000_000_000
    mock_w3.eth.account.from_key.return_value = MagicMock(
        address="0x" + "d" * 40
    )
    signed = MagicMock()
    signed.raw_transaction = b"\x00" * 32
    mock_w3.eth.account.from_key.return_value.sign_transaction.return_value = signed
    mock_w3.eth.send_raw_transaction.return_value = b"\xff" * 32
    receipt = MagicMock()
    receipt.status = tx_status
    mock_w3.eth.wait_for_transaction_receipt.return_value = receipt

    contract = MagicMock()
    contract.functions.redeemPositions.return_value.build_transaction.return_value = {}
    mock_w3.eth.contract.return_value = contract
    return mock_w3


def test_standard_redeem_success():
    mock_w3 = _mock_web3(tx_status=1)
    with patch("redemption.Web3") as MockWeb3:
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider.return_value = MagicMock()
        MockWeb3.to_checksum_address.side_effect = lambda x: x
        result = redeem_position_sync(_make_position(neg_risk=False), PRIVATE_KEY, RPC_URL)
    assert result is True


def test_neg_risk_redeem_success():
    mock_w3 = _mock_web3(tx_status=1)
    with patch("redemption.Web3") as MockWeb3:
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider.return_value = MagicMock()
        MockWeb3.to_checksum_address.side_effect = lambda x: x
        result = redeem_position_sync(_make_position(neg_risk=True), PRIVATE_KEY, RPC_URL)
    assert result is True


def test_reverted_tx_returns_false():
    mock_w3 = _mock_web3(tx_status=0)
    with patch("redemption.Web3") as MockWeb3:
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider.return_value = MagicMock()
        MockWeb3.to_checksum_address.side_effect = lambda x: x
        result = redeem_position_sync(_make_position(), PRIVATE_KEY, RPC_URL)
    assert result is False


def test_rpc_not_connected_returns_false():
    mock_w3 = _mock_web3(connected=False)
    with patch("redemption.Web3") as MockWeb3:
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider.return_value = MagicMock()
        result = redeem_position_sync(_make_position(), PRIVATE_KEY, RPC_URL)
    assert result is False
