import random
import re

from urlshortener.encoding.base62 import decode, encode

_MAX_INT64 = 2**63 - 1


def test_pivot_id_is_five_to_seven_base62_characters():
    code = encode(56800235)
    assert re.fullmatch(r"[0-9A-Za-z]+", code)
    assert 5 <= len(code) <= 7


def test_alphabet_has_no_base64_symbols():
    code = encode(56800235)
    assert "+" not in code
    assert "/" not in code


def test_max_signed_64_bit_round_trip():
    assert decode(encode(_MAX_INT64)) == _MAX_INT64


def test_round_trip_random_positive_ids():
    generator = random.Random(56800235)
    for _ in range(30):
        value = generator.randint(1, _MAX_INT64)
        assert decode(encode(value)) == value


def test_zero_encodes_as_zero():
    assert encode(0) == "0"
    assert decode("0") == 0
