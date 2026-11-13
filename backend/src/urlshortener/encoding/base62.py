"""Deterministic Base62 conversion of a numeric id."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_INDEX = {character: index for index, character in enumerate(ALPHABET)}


def encode(value: int) -> str:
    """Encode a non-negative integer. ``encode(0)`` is ``0``."""
    if value < 0:
        raise ValueError("id must be non-negative")
    if value == 0:
        return "0"
    characters: list[str] = []
    remaining = value
    while remaining > 0:
        characters.append(ALPHABET[remaining % 62])
        remaining //= 62
    return "".join(reversed(characters))


def decode(code: str) -> int:
    """Inverse of :func:`encode`."""
    if code == "":
        raise ValueError("short code is empty")
    total = 0
    for character in code:
        try:
            total = total * 62 + _INDEX[character]
        except KeyError as exc:
            raise ValueError("short code is not Base62") from exc
    return total
