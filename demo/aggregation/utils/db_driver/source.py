"""This module provides the Source enum"""

from enum import Enum


class Source(Enum):
    """Encode possible sources of articles and urls"""

    WATSON = "Watson"
    ZWANZIG_MIN = "20min"
    BLICK = "blick"
    SRF = "srf"
