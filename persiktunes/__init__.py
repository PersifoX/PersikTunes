"""
PersikTunes
~~~~~~
The modern Lavalink wrapper designed for disnake.

Copyright (c) 2024, persifox

Licensed under GPL-3.0
"""

import disnake

if not disnake.version_info.major >= 2:

    class DiscordPyOutdated(Exception):
        pass

    raise DiscordPyOutdated(
        "You must have disnake (v2.0 or greater) to use this library. "
        "Uninstall your current version and install disnake 2.0 "
        "using 'pip install disnake[voice]'",
    )

__version__ = "2.7.2"
__title__ = "PersikTunes"
__author__ = "persifox"
__license__ = "GPL-3.0"
__copyright__ = "Copyright (c) 2024, persifox"

from .clients import *
from .enums import *
from .events import *
from .exceptions import *
from .filters import *
from .models import *
from .objects import *
from .player import *
from .pool import *
from .queue import *
from .routeplanner import *
from .search import *
