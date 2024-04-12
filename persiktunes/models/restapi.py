from pydantic import BaseModel
from typing import Optional, Any, Literal, Union, List

"""
LAVALINK BASE MODELS
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
    isrc = Optional[str] = None
    sourceName = str = None


class LavalinkPlaylistInfo(BaseModel):
    """Base lavalink playlist info model."""

    name: str
    selectedTrack: Optional[int] = -1


class LavalinkTrack(BaseModel):
    """Base lavalink track model."""

    encoded: str
    info: LavalinkTrackInfo
    pluginInfo: Optional[Any] = None
    userData: Optional[Any] = None


class LavalinkPlaylist(BaseModel):
    """Base lavalink playlist model."""

    info: LavalinkPlaylistInfo
    pluginInfo: Optional[Any] = None
    tracks: List[LavalinkTrack]


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
            LavalinkTrack,
            LavalinkPlaylist,
            List[LavalinkTrack],
            LavalinkExceptionResponse,
        ]
    ] = {}


class LavalinkTrackDecodeResponse(LavalinkTrack):
    """Response model is analog to LavalinkTrack."""


class LavalinkTrackDecodeMultiplyResponse(BaseModel):
    """Base lavalink track decode multiply response model."""

    tracks: List[LavalinkTrack]


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
LAVALINK PLAYER API
"""


class LavalinkPlayer(BaseModel):
    guildId: int
    track: Optional[LavalinkTrack] = None
    volume: int
    paused: bool
    state: PlayerState
    voice: VoiceState
    filters: Filters
