"""All interactions with API behind atsu.

This class is usually a wrapper of an existing SDK, or a raw implementation of it to have reusable code in the worker.py.
"""

import logging


logger = logging.getLogger("nautobot")


class NautobotChatopsAtsu:  # pylint: disable=too-few-public-methods
    """Representation and methods for interacting with the API behind atsu."""

    def __init__(self):
        """Initialization of atsu class."""
