"""
### Enums Module `main`

This module contains all the enums used in PersikTunes.
"""

import re
from enum import Enum, IntEnum


class SearchType(Enum):
    """
    ## The enum for the different search types for PersikTunes.
    This feature is exclusively for the Spotify search feature of PersikTunes.
    If you are not using this feature, this class is not necessary.

    ------------
    `SearchType.ytsearch` searches using regular Youtube,
    which is best for all scenarios.

    `SearchType.ytmsearch` searches using YouTube Music,
    which is best for getting audio-only results.

    `SearchType.scsearch` searches using SoundCloud,
    which is an alternative to YouTube or YouTube Music.

    ~~~~~~~~~~~~~
    #### LavaSRC adds support for the following search types:

    `SearchType.spsearch` searches using Spotify,
    but playback via youtube.

    `SearchType.amsearch` searches using Apple Music,
    also playback via youtube.

    `SearchType.dzsearch` searches using Deezer,
    which is an alternative.

    `SearchType.ymsearch` searches using Yandex Music,
    which is an alternative.

    ~~~~~~~~~~~~~
    #### Special

    `SearchType.sprec` searches recommendations using Spotify,
    check the Spotify documentation for more information.

    `SearchType.ftts` searches using Flowery TTS,
    unstable and not recommended.
    """

    ytsearch = "ytsearch"
    ytmsearch = "ytmsearch"
    scsearch = "scsearch"

    spsearch = "spsearch"
    amsearch = "amsearch"
    dzsearch = "dzsearch"
    ymsearch = "ymsearch"

    sprec = "sprec"

    ftts = "ftts"

    def __str__(self) -> str:
        return self.value


class TrackType(Enum):
    """
    ## The enum for the different track types for PersikTunes.

    ~~~~~~~~~~~
    `TrackType.YOUTUBE` defines that the track is from YouTube

    `TrackType.SOUNDCLOUD` defines that the track is from SoundCloud.

    `TrackType.SPOTIFY` defines that the track is from Spotify

    `TrackType.APPLE_MUSIC` defines that the track is from Apple Music.

    `TrackType.TWITCH` defines that the stream is from Twitch.

    `TrackType.TTS` defines tts file from Flowery TTS.

    `TrackType.DEZEER` defines that the track is from Deezer.

    `TrackType.YANDEX_MUSIC` defines that the track is from Yandex Music.

    `TrackType.HTTP` defines that the track is from an HTTP source.

    `TrackType.LOCAL` defines that the track is from a local source.
    """

    # We don't have to define anything special for these, since these just
    # serve as flags
    YOUTUBE = "youtube"
    SOUNDCLOUD = "soundcloud"
    SPOTIFY = "spotify"
    DEZEER = "dezeer"
    YANDEX_MUSIC = "yandexmusic"
    APPLE_MUSIC = "apple_music"
    TWITCH = "twitch"
    TTS = "ftts"
    HTTP = "http"
    LOCAL = "local"

    def __str__(self) -> str:
        return self.value


class PlaylistType(Enum):
    """
    ## The enum for the different playlist types for PersikTunes.

    `PlaylistType.YOUTUBE` defines that the playlist is from YouTube

    `PlaylistType.SOUNDCLOUD` defines that the playlist is from SoundCloud.

    `PlaylistType.SPOTIFY` defines that the playlist is from Spotify

    `PlaylistType.APPLE_MUSIC` defines that the playlist is from Apple Music.

    `PlaylistType.YANDEX_MUSIC` defines that the playlist is from Yandex Music.
    """

    # We don't have to define anything special for these, since these just
    # serve as flags
    YOUTUBE = "youtube"
    SOUNDCLOUD = "soundcloud"
    SPOTIFY = "spotify"
    YANDEX_MUSIC = "yandex_music"
    APPLE_MUSIC = "apple_music"

    def __str__(self) -> str:
        return self.value


class NodeAlgorithm(Enum):
    """
    ## The enum for the different node algorithms in PersikTunes.

    The enums in this class are to only differentiate different
    methods, since the actual method is handled in the
    `get_best_node()` method.

    `NodeAlgorithm.by_ping` returns a node based on it's latency,
    preferring a node with the lowest response time


    `NodeAlgorithm.by_players` return a nodes based on how many players it has.
    This algorithm prefers nodes with the least amount of players.
    """

    # We don't have to define anything special for these, since these just
    # serve as flags
    by_ping = "BY_PING"
    by_players = "BY_PLAYERS"

    def __str__(self) -> str:
        return self.value


class LoopMode(Enum):
    """
    ## The enum for the different loop modes.
    This feature is exclusively for the queue utility of PersikTunes.
    If you are not using this feature, this class is not necessary.

    `LoopMode.TRACK` sets the queue loop to the current track.

    `LoopMode.QUEUE` sets the queue loop to the whole queue.

    """

    # We don't have to define anything special for these, since these just
    # serve as flags
    TRACK = "track"
    QUEUE = "queue"

    def __str__(self) -> str:
        return self.value


class RouteStrategy(Enum):
    """
    ## The enum for specifying the route planner strategy for Lavalink.
    This feature is exclusively for the RoutePlanner class.
    If you are not using this feature, this class is not necessary.

    `RouteStrategy.ROTATE_ON_BAN` specifies that the node is rotating IPs
    whenever they get banned by Youtube.

    `RouteStrategy.LOAD_BALANCE` specifies that the node is selecting
    random IPs to balance out requests between them.

    `RouteStrategy.NANO_SWITCH` specifies that the node is switching
    between IPs every CPU clock cycle.

    `RouteStrategy.ROTATING_NANO_SWITCH` specifies that the node is switching
    between IPs every CPU clock cycle and is rotating between IP blocks on
    ban.

    """

    ROTATE_ON_BAN = "RotatingIpRoutePlanner"
    LOAD_BALANCE = "BalancingIpRoutePlanner"
    NANO_SWITCH = "NanoIpRoutePlanner"
    ROTATING_NANO_SWITCH = "RotatingNanoIpRoutePlanner"


class RouteIPType(Enum):
    """
    ## The enum for specifying the route planner IP block type for Lavalink.
    This feature is exclusively for the RoutePlanner class.
    If you are not using this feature, this class is not necessary.

    `RouteIPType.IPV4` specifies that the IP block type is IPV4

    `RouteIPType.IPV6` specifies that the IP block type is IPV6
    """

    IPV4 = "Inet4Address"
    IPV6 = "Inet6Address"


class URLRegex:
    """
    ## The enum for all the URL Regexes in use by PersikTunes.

    `URLRegex.SPOTIFY_URL` returns the Spotify URL Regex.

    `URLRegex.DISCORD_MP3_URL` returns the Discord MP3 URL Regex.

    `URLRegex.YOUTUBE_URL` returns the Youtube URL Regex.

    `URLRegex.YOUTUBE_PLAYLIST` returns the Youtube Playlist Regex.

    `URLRegex.YOUTUBE_TIMESTAMP` returns the Youtube Timestamp Regex.

    `URLRegex.AM_URL` returns the Apple Music URL Regex.

    `URLRegex.SOUNDCLOUD_URL` returns the SoundCloud URL Regex.

    `URLRegex.BASE_URL` returns the standard URL Regex.

    `LAVALINK_SEARCH` returns the Lavalink Search Regex.

    `LAVALINK_REC` returns the Lavalink recommendation Regex.

    `LAVALINK_TTS` returns the Lavalink TTS Regex.

    """

    SPOTIFY_URL = re.compile(
        r"https?://open.spotify.com/(?P<type>album|playlist|track|artist)/(?P<id>[a-zA-Z0-9]+)",
    )

    DISCORD_MP3_URL = re.compile(
        r"https?://cdn.discordapp.com/attachments/(?P<channel_id>[0-9]+)/"
        r"(?P<message_id>[0-9]+)/(?P<file>[a-zA-Z0-9_.]+)+",
    )

    YOUTUBE_URL = re.compile(
        r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))"
        r"(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$",
    )

    YOUTUBE_PLAYLIST_URL = re.compile(
        r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))/playlist\?list=.*",
    )

    YOUTUBE_TIMESTAMP = re.compile(
        r"(?P<video>^.*?)(\?t|&start)=(?P<time>\d+)?.*",
    )

    AM_URL = re.compile(
        r"https?://music.apple.com/(?P<country>[a-zA-Z]{2})/"
        r"(?P<type>album|playlist|song|artist)/(?P<name>.+)/(?P<id>[^?]+)",
    )

    AM_SINGLE_IN_ALBUM_REGEX = re.compile(
        r"https?://music.apple.com/(?P<country>[a-zA-Z]{2})/(?P<type>album|playlist|song|artist)/"
        r"(?P<name>.+)/(?P<id>.+)(\?i=)(?P<id2>.+)",
    )

    SOUNDCLOUD_URL = re.compile(
        r"((?:https?:)?\/\/)?((?:www|m)\.)?soundcloud.com\/.*/.*",
    )

    SOUNDCLOUD_PLAYLIST_URL = re.compile(
        r"^(https?:\/\/)?(www.)?(m\.)?soundcloud\.com\/.*/sets/.*",
    )

    SOUNDCLOUD_TRACK_IN_SET_URL = re.compile(
        r"^(https?:\/\/)?(www.)?(m\.)?soundcloud\.com/[a-zA-Z0-9-._]+/[a-zA-Z0-9-._]+(\?in)",
    )

    LAVALINK_SEARCH = re.compile(r"^(yt|ytm|sc|sp|dz|am)search:.*$")

    LAVALINK_REC = re.compile(r"^(yt|ytm|sc|sp|dz|am)rec:.*$")

    LAVALINK_TTS = re.compile(r"^ftts:.*$")

    BASE_URL = re.compile(r"https?://(?:www\.)?.+")


class LogLevel(IntEnum):
    """
    ## The enum for specifying the logging level within PersikTunes.
    This class serves as shorthand for logging.<level>
    This enum is exclusively for the logging feature in PersikTunes.
    If you are not using this feature, this class is not necessary.


    `LogLevel.DEBUG` sets the logging level to "debug".

    `LogLevel.INFO` sets the logging level to "info".

    `LogLevel.WARN` sets the logging level to "warn".

    `LogLevel.ERROR` sets the logging level to "error".

    `LogLevel.CRITICAL` sets the logging level to "CRITICAL".

    """

    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    CRITICAL = 50
