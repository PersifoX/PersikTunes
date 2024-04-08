"""
### Models module `main`

This module contains all the pydantic models used in PersikTunes.
"""

from pydantic import BaseModel
from typing import Optional, Any, Literal, Union, List

# __all__ = (
#     "Track",
#     "Playlist",
#     "Author",
# )

"""
LAVALINK BASE MODELS (prefixes with Base)
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
