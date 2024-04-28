from typing import Any, AnyStr, List, Literal, Optional, Union
from uuid import uuid4

from disnake import ClientUser, Interaction, Member, User
from disnake.ext import commands
from pydantic import BaseModel

"""
LAVALINK BASE MODELS
"""


class ExtraModel(BaseModel):
    """Alows arbitrary types in pydantic models."""


ExtraModel.model_config["arbitrary_types_allowed"] = True


"FILTERS MODELS"


class EqualizerBand(BaseModel):
    band: int
    gain: float


class Karaoke(BaseModel):
    level: Optional[float] = None
    monoLevel: Optional[float] = None
    filterBand: Optional[float] = None
    filterWidth: Optional[float] = None


class Timescale(BaseModel):
    speed: Optional[float] = None
    pitch: Optional[float] = None
    rate: Optional[float] = None


class Tremolo(BaseModel):
    frequency: Optional[float] = None
    depth: Optional[float] = None


class Vibrato(BaseModel):
    frequency: Optional[float] = None
    depth: Optional[float] = None


class Rotation(BaseModel):
    rotationHz: Optional[float] = None


class Distortion(BaseModel):
    sinOffset: Optional[float] = None
    sinScale: Optional[float] = None
    cosOffset: Optional[float] = None
    cosScale: Optional[float] = None
    tanOffset: Optional[float] = None
    tanScale: Optional[float] = None
    offset: Optional[float] = None
    scale: Optional[float] = None


class ChannelMix(BaseModel):
    leftToLeft: Optional[float] = None
    leftToRight: Optional[float] = None
    rightToLeft: Optional[float] = None
    rightToRight: Optional[float] = None


class LowPass(BaseModel):
    smoothing: Optional[float] = None


class Filters(BaseModel):
    volume: Optional[float] = 1.0
    equalizer: Optional[List[EqualizerBand]] = None
    karaoke: Optional[Karaoke] = None
    timescale: Optional[Timescale] = None
    tremolo: Optional[Tremolo] = None
    vibrato: Optional[Vibrato] = None
    rotation: Optional[Rotation] = None
    distortion: Optional[Distortion] = None
    channelMix: Optional[ChannelMix] = None
    lowPass: Optional[LowPass] = None
    pluginFilters: Optional[Any] = None


"""
LAVALINK INFO MODELS
"""


class LavalinkTrackInfo(BaseModel):
    """Base lavalink track info model."""

    identifier: str
    isSeekable: bool
    author: str
    length: int
    isStream: bool
    position: int
    title: str
    uri: Optional[str] = None
    artworkUrl: Optional[str] = None
    isrc: Optional[str] = None
    sourceName: str = None


class LavalinkPlaylistInfo(BaseModel):
    """Base lavalink playlist info model."""

    name: str
    selectedTrack: Optional[int] = -1


"""
LAVALINK MAIN MODELS
"""


class Track(ExtraModel):
    """Base lavalink track model."""

    uuid: str = uuid4().__str__()  # Unique uuid for the track

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    encoded: str
    info: LavalinkTrackInfo
    pluginInfo: Optional[Any] = None
    userData: Optional[Any] = None
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    lyrics: Optional[dict] = None

    ctx: Optional[Union[commands.Context, Interaction]] = None  # Additional context
    requester: Optional[Union[Member, User, ClientUser]] = None  # Additional requester

    filters: Optional[Filters] = None  # Additional filters

    playlist: Optional["Playlist"] = None

    description: Optional[str] = None  # Optional track description

    color: Optional[int] = None  # Track color

    tag: Optional[AnyStr] = None  # Optional track tag

    @property
    def title(self) -> str:
        """Title of track"""
        return self.info.title

    @property
    def author(self) -> str:
        """Author of track"""
        return self.info.author

    @property
    def length(self) -> int:
        """Length of track"""
        return self.info.length

    @property
    def uri(self) -> str:
        """URI of track"""
        return self.info.uri

    @property
    def thumbnail(self) -> str:
        """Thumbnail of track (artwork)"""
        return self.info.artworkUrl

    @property
    def isrc(self) -> str:
        """ISRC of track"""
        return self.info.isrc

    @property
    def is_stream(self) -> bool:
        """Is track a stream?"""
        return self.info.isStream

    @property
    def position(self) -> int:
        """Position of timeline"""
        return self.info.position

    @property
    def is_seekable(self) -> bool:
        """Is track seekable?"""
        return self.info.isSeekable

    @property
    def source_name(self) -> str:
        return self.info.sourceName

    @property
    def identifier(self) -> str:
        """Identifier of track"""
        return self.info.identifier

    @property
    def tag(self) -> str | None:
        """Tag of track"""
        return self.tag

    @property
    def color(self) -> int | None:
        """Color of track"""
        return self.color

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Track):
            return False

        return other.uuid == self.uuid

    def __str__(self) -> str:
        return self.info.title

    def __repr__(self) -> str:
        return f"<PersikTunes.track title={self.info.title!r} uri=<{self.info.uri!r}> length={self.info.length}>"


class Playlist(ExtraModel):
    """Base lavalink playlist model."""

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    info: LavalinkPlaylistInfo
    pluginInfo: Optional[Any] = None
    tracks: List[Track] = []
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    length: int

    uri: Optional[str] = None
    ctx: Optional[Union[commands.Context, Interaction]] = None  # Additional context
    requester: Optional[Union[Member, User, ClientUser]] = None  # Additional requester

    description: Optional[str] = None  # Optional playlist description

    color: Optional[int] = None  # Playlist color

    tag: Optional[AnyStr] = None  # Optional playlist tag

    @property
    def length(self) -> int:
        """Length of playlist"""
        return sum([t.info.length for t in self.tracks])

    @property
    def name(self) -> str:
        """Name of playlist"""
        return self.info.name

    @property
    def selected_track(self) -> int:
        """Selected track of playlist"""
        return self.info.selectedTrack

    @property
    def track_count(self) -> int:
        """Count of tracks in playlist"""
        return len(self.tracks)

    @property
    def thumbnail(self) -> str | None:
        """Thumbnail of playlist (artwork)"""
        return self.pluginInfo.get("artworkUrl") if self.pluginInfo else None

    @property
    def color(self) -> int | None:
        """Color of playlist"""
        return self.color

    def __str__(self) -> str:
        return self.info.name

    def __repr__(self) -> str:
        return f"<PersikTunes.playlist name={self.info.name!r} track_count={len(self.tracks)}>"


"""
LAVALINK RESPONSES MODELS
"""


class LavalinkResponseError(BaseModel):
    """Base lavalink error model."""

    timestamp: int
    status: int
    error: str
    trace: Optional[str] = None
    message: str
    path: str


class LavalinkExceptionResponse(BaseModel):
    """Base lavalink exception response model."""

    message: str
    severity: Literal["common", "suspicious", "fault"]
    cause: str


class LavalinkTrackLoadingResponse(BaseModel):
    """Base lavalink track loading response model."""

    loadType: Literal["track", "playlist", "search", "empty", "error"]
    data: Optional[
        Union[
            Track,
            Playlist,
            List[Track],
            LavalinkExceptionResponse,
        ]
    ] = {}


class LavalinkTrackDecodeResponse(Track):
    """Response model is analog to LavalinkTrack."""


class LavalinkTrackDecodeMultiplyResponse(BaseModel):
    """Base lavalink track decode multiply response model."""

    tracks: List[Track]


"""
LAVALINK PLAYER ALI MODELS
"""


class VoiceState(BaseModel):
    token: str
    endpoint: str
    sessionId: str


class PlayerState(BaseModel):
    time: int
    position: int
    connected: bool
    ping: int


"""
LAVALINK PLAYER API
"""


class LavalinkPlayer(ExtraModel):
    guildId: int
    track: Optional[Track] = None
    volume: int
    paused: bool
    state: PlayerState
    voice: VoiceState
    filters: Filters


"""
LAVALINK REST API
"""


class UpdatePlayerTrack(BaseModel):
    encoded: Optional[str] = None
    identifier: Optional[str] = None
    userData: Optional[Track] = None


class BaseRestRequest(BaseModel):
    method: Literal["GET", "POST", "PUT", "DELETE"]


class BaseRestResponse(BaseModel):
    pass


class GetPlayersResponse(BaseRestResponse):
    players: List[LavalinkPlayer]


class GetPlayerResponse(BaseRestResponse):
    player: LavalinkPlayer


class UpdatePlayerResponse(BaseRestResponse):
    player: LavalinkPlayer


class UpdatePlayerRequest(BaseRestRequest):
    method: str = "PATCH"
    noReplase: bool = False
    track: Optional[UpdatePlayerTrack] = None
    position: int = 0
    endTime: Optional[int] = None
    volume: Optional[int] = None
    pause: Optional[bool] = None
    filters: Optional[Filters] = None
    voice: Optional[VoiceState] = None


class DeletePlayerRequest(BaseRestRequest):
    method: str = "DELETE"


class UpdateSessionRequest(BaseRestRequest):
    method: str = "PATCH"
    resuming: Optional[bool] = False
    timeout: Optional[int] = 60


class UpdateSessionResponse(BaseRestResponse):
    resuming: bool
    timeout: int


class GetLavalinkVersionRequest(BaseRestRequest):
    method: str = "GET"


class GetTracksRequest(BaseRestRequest):
    method: str = "GET"


class GetLavalinkVersionResponse(BaseRestResponse):
    pass


class GetLavalinkStatsRequest(BaseRestRequest):
    method: str = "GET"
