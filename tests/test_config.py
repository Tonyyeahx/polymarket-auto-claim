import pytest
from pydantic import ValidationError
from unittest.mock import patch
import config as cfg


def _make_env(**extra):
    base = {
        "PRIVATE_KEY": "0x" + "a" * 64,
        "WALLET_ADDRESS": "0x" + "b" * 40,
    }
    base.update(extra)
    return base


def setup_function():
    cfg.reset_settings()


def teardown_function():
    cfg.reset_settings()


def test_config_loads_required_fields():
    with patch.dict("os.environ", _make_env(), clear=True):
        s = cfg.Settings(_env_file=None)
        assert s.private_key.get_secret_value() == "0x" + "a" * 64
        assert s.wallet_address == "0x" + "b" * 40
        assert s.polygon_rpc_url == "https://polygon-rpc.com"
        assert s.poll_interval == 300


def test_config_custom_poll_interval():
    with patch.dict("os.environ", _make_env(POLL_INTERVAL="60"), clear=True):
        s = cfg.Settings(_env_file=None)
        assert s.poll_interval == 60


def test_config_missing_private_key_raises():
    with patch.dict("os.environ", {"WALLET_ADDRESS": "0x" + "b" * 40}, clear=True):
        with pytest.raises(ValidationError):
            cfg.Settings(_env_file=None)


def test_poll_interval_below_minimum_raises():
    with patch.dict("os.environ", _make_env(POLL_INTERVAL="9"), clear=True):
        with pytest.raises(ValidationError):
            cfg.Settings(_env_file=None)
