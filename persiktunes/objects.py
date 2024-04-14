"""
### Objects module `legacy`

This module contains all the objects used in PersikTunes.
"""

from __future__ import annotations

from typing import List, Optional, Union
from uuid import UUID, uuid4

from disnake import ClientUser, Interaction, Member, User
from disnake.ext import commands

from .enums import PlaylistType, SearchType, TrackType
from .filters import Filter


class Author:
    """The base author object. Returns author information needed for parsing by Lavalink plugin."""

    def __init__(
        self,
        *,
        name: str,
        type: str,
        avatar: Optional[str] = None,
        url: Optional[str] = None,
    ):

        self.name: str = name
        self.type: str = type

        self.avatar: Optional[str] = avatar
        self.url: Optional[str] = url

    def __str__(self) -> str:
        return self.name


class Track:
    """The base track object. Returns critical track information needed for parsing by Lavalink.
    You can also pass in commands.Context to get a disnake Context object in your track.
    """

    def __init__(
        self,
        *,
        track_id: str,
        info: dict,
        plugin_info: Optional[dict] = None,
        ctx: Optional[Union[commands.Context, Interaction]] = None,
        track_type: TrackType,
        search_type: SearchType = SearchType.ytsearch,
        playlist: Optional[Playlist] = None,
        filters: Optional[List[Filter]] = None,
        timestamp: Optional[float] = None,
        requester: Optional[Union[Member, User, ClientUser]] = None,
        lyrics: Optional[str] = None,
    ):
        self.track_id: str = track_id
        self.info: dict = info
        self.plugin_info: Optional[dict] = plugin_info
        self.track_type: TrackType = track_type
        self.filters: Optional[List[Filter]] = filters
        self.timestamp: Optional[float] = timestamp
        self.lyrics: Optional[str] = lyrics

        self.original = self

        self._search_type: SearchType = search_type

        self.playlist: Optional[Playlist] = playlist

        self.title: str = info.get("title", "Unknown Title")
        self.author: Union[str, Author] = info.get("author", "Unknown Author")
        self.uri: str = info.get("uri", "")
        self.identifier: str = info.get("identifier", "")
        self.isrc: Optional[str] = info.get("isrc", None)
        self.thumbnail: Optional[str] = info.get("artworkUrl")

        if plugin_info and plugin_info.get("artistUrl"):
            self.author = Author(
                name=self.author,
                type=self.track_type.value,
                avatar=plugin_info.get("artistArtworkUrl"),
                url=plugin_info.get("artistUrl"),
            )

        self.length: int = info.get("length", 0)
        self.is_stream: bool = info.get("isStream", False)
        self.is_seekable: bool = info.get("isSeekable", False)
        self.position: int = info.get("position", 0)

        self.ctx: Optional[Union[commands.Context, Interaction]] = ctx
        self.requester: Optional[Union[Member, User, ClientUser]] = requester
        if not self.requester and self.ctx:
            self.requester = self.ctx.author

        self.uuid: UUID = uuid4()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Track):
            return False

        return other.uuid == self.uuid

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f"<PersikTunes.track title={self.title!r} uri=<{self.uri!r}> length={self.length}>"

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the track."""
        return {
            "title": self.title,
            "author": self.author.__str__(),
            "thumbnail": self.thumbnail,
            "url": self.uri,
            "id": self.track_id,
            "length": self.length,
            "playlist": self.playlist.name if self.playlist else None,
            "type": self.track_type.value,
        }


class Playlist:
    """The base playlist object.
    Returns critical playlist information needed for parsing by Lavalink.
    You can also pass in commands.Context to get a disnake Context object in your tracks.
    """

    def __init__(
        self,
        *,
        playlist_info: dict,
        tracks: list,
        playlist_type: PlaylistType,
        thumbnail: Optional[str] = None,
        uri: Optional[str] = None,
    ):
        self.playlist_info: dict = playlist_info
        self.tracks: List[Track] = tracks
        self.name: str = playlist_info.get("name", "Unknown Playlist")
        self.author: str = playlist_info.get("author", "Unknown Author")
        self.playlist_type: PlaylistType = playlist_type

        self._thumbnail: Optional[str] = thumbnail
        self._uri: Optional[str] = uri

        self.length: float = 0

        for track in self.tracks:
            track.playlist = self
            self.length += track.length

        self.selected_track: Optional[Track] = None
        if (index := playlist_info.get("selectedTrack", -1)) != -1:
            self.selected_track = self.tracks[index]

        self.track_count: int = len(self.tracks)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (
            f"<PersikTunes.playlist name={self.name!r} track_count={len(self.tracks)}>"
        )

    @property
    def uri(self) -> Optional[str]:
        """Returns either an URL/URI, or None if its neither of those."""
        return self._uri

    @property
    def thumbnail(self) -> Optional[str]:
        """Returns either an album/playlist thumbnail, or None if its neither of those."""
        return self._thumbnail

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the playlist."""
        return {
            "name": self.name,
            "author": self.author,
            "uri": self.uri,
            "length": self.length,
            "thumbnail": self.thumbnail,
            "playlist_type": self.playlist_type,
            "tracks": [track.to_dict() for track in self.tracks],
        }
