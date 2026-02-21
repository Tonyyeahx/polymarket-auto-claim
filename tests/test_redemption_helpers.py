from redemption import _outcome_to_index_sets, _condition_id_to_bytes32


def test_outcome_yes():
    assert _outcome_to_index_sets("YES") == [1]
    assert _outcome_to_index_sets("yes") == [1]


def test_outcome_no():
    assert _outcome_to_index_sets("NO") == [2]
    assert _outcome_to_index_sets("no") == [2]


def test_outcome_unknown():
    assert _outcome_to_index_sets("other") == [1, 2]


def test_condition_id_without_prefix():
    hex_val = "a" * 64
    result = _condition_id_to_bytes32(hex_val)
    assert isinstance(result, bytes)
    assert len(result) == 32
    assert result == bytes.fromhex("a" * 64)


def test_condition_id_with_0x_prefix():
    hex_val = "0x" + "b" * 64
    result = _condition_id_to_bytes32(hex_val)
    assert result == bytes.fromhex("b" * 64)


def test_condition_id_short_is_zero_padded():
    hex_val = "0xabcd"
    result = _condition_id_to_bytes32(hex_val)
    assert len(result) == 32
    assert result[-2:] == bytes.fromhex("abcd")
