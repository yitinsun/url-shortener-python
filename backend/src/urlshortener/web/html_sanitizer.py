"""Reject markup in longUrl. Do not rewrite the value."""

import warnings

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning


def looks_unsafe(value: str) -> bool:
    if not isinstance(value, str):
        return False
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", MarkupResemblesLocatorWarning)
        soup = BeautifulSoup(value, "html.parser")
    return soup.find(True) is not None
