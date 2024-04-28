"""
### Pool module `main`

This module contains all the pool used in PersikTunes.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from os import path
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Type,
    Union,
)
from urllib.parse import quote

import aiohttp
import typing_extensions
from disnake import Client, ClientUser, Interaction, Member, User
from disnake.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials

from . import __version__
from .clients.rest import LavalinkRest
from .clients.ws import LavalinkWebsocket
from .enums import *
from .enums import LogLevel
from .exceptions import (
    LavalinkVersionIncompatible,
    NodeCreationError,
    NodeNotAvailable,
    NodeRestException,
    NoNodesAvailable,
    TrackLoadError,
)
from .filters import Filter
from .models.restapi import Playlist, Track
from .routeplanner import RoutePlanner
from .utils import LavalinkVersion, NodeStats, Ping

if TYPE_CHECKING:
    from .player import Player

VERSION_REGEX = re.compile(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[a-zA-Z0-9_-]+)?")


class Node:
    """The base class for a node.
    This node object represents a Lavalink node.
    `external` arrtibute is an instance for searching tracks via python instead lavalink
    """

    def __init__(
        self,
        *,
        pool: Type[NodePool],
        bot: commands.Bot,
        host: str,
        port: int,
        password: str,
        identifier: str,
        secure: bool = False,
        heartbeat: int = 120,
        resume_key: Optional[str] = None,
        resume_timeout: int = 60,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        session: Optional[aiohttp.ClientSession] = None,
        fallback: bool = False,
        spotify_credentials: Optional[SpotifyClientCredentials] = None,
        log_level: LogLevel = LogLevel.INFO,
        log_handler: Optional[logging.Handler] = None,
        setup_logging: Optional[Callable] = None,
    ):
        if not isinstance(port, int):
            raise TypeError("Port must be an integer")

        self._bot: commands.Bot = bot
        self._host: str = host
        self._port: int = port
        self._pool: Type[NodePool] = pool
        self._password: str = password
        self._identifier: str = identifier
        self._heartbeat: int = heartbeat
        self._resume_key: Optional[str] = resume_key
        self._resume_timeout: int = resume_timeout
        self._secure: bool = secure
        self._fallback: bool = fallback
        self._spotify_credentials: Optional[SpotifyClientCredentials] = (
            spotify_credentials
        )

        self._setup_logging = setup_logging or self._setup_logging

        self._log_level: LogLevel = log_level
        self._log_handler = log_handler

        self._rest_uri: str = (
            f"{'https' if self._secure else 'http'}://{self._host}:{self._port}"
        )

        self._session: aiohttp.ClientSession = session  # type: ignore
        self._loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()
        self._task: asyncio.Task = None  # type: ignore

        self._session_id: Optional[str] = None
        self._available: bool = False
        self._version: LavalinkVersion = LavalinkVersion(0, 0, 0)

        self._route_planner = RoutePlanner(self)
        self._log = self._setup_logging(self._log_level)

        if not self._bot.user:
            raise NodeCreationError("Bot user is not ready yet.")

        self._bot_user = self._bot.user

        self._players: Dict[int, Player] = {}

        self._websocket: LavalinkWebsocket = LavalinkWebsocket(
            self,
            self._host,
            self._port,
            self._password,
            self._bot.user.id,
            secure,
            heartbeat,
            resume_key,
            resume_timeout,
            loop,
            session,
            fallback,
            log_level=log_level,
            setup_logging=self._setup_logging,
        )

        self._rest: LavalinkRest = LavalinkRest(
            self,
            self._host,
            self._port,
            self._password,
            self._bot.user.id,
            secure,
            loop,
            session,
            fallback,
            log_level=log_level,
            setup_logging=self._setup_logging,
        )

    def __repr__(self) -> str:
        return (
            f"<PersikTunes.node ws_uri={self._websocket._websocket_uri} rest_uri={self._rest_uri}"
            f"player_count={len(self._players)}>"
        )

    @property
    def is_connected(self) -> bool:
        """Property which returns whether this node is connected or not"""
        return self._websocket.is_connected

    @property
    def stats(self) -> NodeStats:
        """Property which returns the node stats."""
        return self._websocket._stats

    @property
    def players(self) -> Dict[int, Player]:
        """Property which returns a dict containing the guild ID and the player object."""
        return self._players

    @property
    def bot(self) -> Client:
        """Property which returns the disnake client linked to this node"""
        return self._bot

    @property
    def player_count(self) -> int:
        """Property which returns how many players are connected to this node"""
        return len(self.players.values())

    @property
    def pool(self) -> NodePool:
        """Property which returns the pool this node is apart of"""
        return self._pool

    @property
    def latency(self) -> float:
        """Property which returns the latency of the node"""
        return Ping(self._host, port=self._port).get_ping()

    @property
    def ping(self) -> float:
        """Alias for `Node.latency`, returns the latency of the node"""
        return self.latency

    @property
    def rest(self) -> LavalinkRest:
        """Property which returns the LavalinkRest object"""
        return self._rest

    def _setup_logging(self, level: LogLevel) -> logging.Logger:
        logger = logging.getLogger("PersikTunes")

        handler = None

        if self._log_handler:
            handler = self._log_handler
            logger.setLevel(handler.level)
        else:
            handler = logging.StreamHandler()
            logger.setLevel(level)
            dt_fmt = "%Y-%m-%d %H:%M:%S"
            formatter = logging.Formatter(
                "[{asctime}] [{levelname:<8}] {name}: {message}",
                dt_fmt,
                style="{",
            )
            handler.setFormatter(formatter)

        if handler:
            logger.handlers.clear()
            logger.addHandler(handler)

        return logger

    async def _handle_version_check(self, version: str) -> None:
        if version.endswith("-SNAPSHOT"):
            # we're just gonna assume all snapshot versions correlate with v4
            self._version = LavalinkVersion(major=4, minor=0, fix=0)
            return

        _version_rx = VERSION_REGEX.match(version)
        if not _version_rx:
            self._available = False
            raise LavalinkVersionIncompatible(
                "The Lavalink version you're using is incompatible. "
                "Lavalink version 3.7.0 or above is required to use this library.",
            )

        _version_groups = _version_rx.groups()
        major, minor, fix = (
            int(_version_groups[0] or 0),
            int(_version_groups[1] or 0),
            int(_version_groups[2] or 0),
        )

        self._log.debug(f"Parsed Lavalink version: {major}.{minor}.{fix}")
        self._version = LavalinkVersion(major=major, minor=minor, fix=fix)
        if self._version < LavalinkVersion(3, 7, 0):
            self._available = False
            raise LavalinkVersionIncompatible(
                "The Lavalink version you're using is incompatible. "
                "Lavalink version 3.7.0 or above is required to use this library.",
            )

        if self._version < LavalinkVersion(4, 0, 0):
            self._log.warn(
                f"Lavalink version {self._version} is not recommended, PersikTunes has been tested with Lavalink 4.0.0 or above."
            )

    async def _configure_resuming(self) -> None:
        if not self._resume_key:
            return

        data = {"timeout": self._resume_timeout}

        if self._version.major == 3:
            data["resumingKey"] = self._resume_key
        elif self._version.major == 4:
            data["resuming"] = True

        await self.send(
            method="PATCH",
            path=f"sessions/{self._session_id}",
            include_version=True,
            data=data,
        )

    @typing_extensions.deprecated("This method is deprecated; use `rest.send` instead.")
    async def send(
        self,
        method: Literal["GET", "POST", "PATCH", "PUT", "DELETE"],
        path: str,
        include_version: bool = True,
        guild_id: Optional[Union[int, str]] = None,
        query: Optional[str] = None,
        data: Optional[Union[Dict, str]] = None,
        ignore_if_available: bool = False,
    ) -> Any:
        if not ignore_if_available and not self._available:
            raise NodeNotAvailable(
                f"The node '{self._identifier}' is unavailable.",
            )

        uri: str = (
            f"{self._rest_uri}/"
            f'{f"v{self._version.major}/" if include_version else ""}'
            f"{path}"
            f'{f"/{guild_id}" if guild_id else ""}'
            f'{f"?{query}" if query else ""}'
        )

        resp = await self._session.request(
            method=method,
            url=uri,
            headers=self._headers,
            json=data or {},
        )
        self._log.debug(
            f"Making REST request to Node {self._identifier} with method {method} to {uri}",
        )
        if resp.status >= 300:
            resp_data: dict = await resp.json()
            raise NodeRestException(
                f'Error from Node {self._identifier} fetching from Lavalink REST api: {resp.status} {resp.reason}: {resp_data["message"]}',
            )

        if method == "DELETE" or resp.status == 204:
            self._log.debug(
                f"REST request to Node {self._identifier} with method {method} to {uri} completed sucessfully and returned no data.",
            )
            return await resp.json(content_type=None)

        if resp.content_type == "text/plain":
            self._log.debug(
                f"REST request to Node {self._identifier} with method {method} to {uri} completed sucessfully and returned text with body {await resp.text()}",
            )
            return await resp.text()

        self._log.debug(
            f"REST request to Node {self._identifier} with method {method} to {uri} completed sucessfully and returned JSON with body {await resp.json()}",
        )
        return await resp.json()

    def get_player(self, guild_id: int) -> Optional[Player]:
        """Takes a guild ID as a parameter. Returns a PersikTunes Player object or None."""
        return self._players.get(guild_id, None)

    @typing_extensions.deprecated(
        "This method is deprecated; use `rest.build_track` instead."
    )
    async def build_track(
        self,
        identifier: str,
        ctx: Optional[Union[commands.Context, Interaction]] = None,
    ) -> Track:
        """
        Builds a track using a valid track identifier

        You can also pass in a disnake Context object to get a
        Context object on the track it builds.
        """

        data: dict = await self.send(
            method="GET",
            path="decodetrack",
            query=f"encodedTrack={quote(identifier)}",
        )

        return Track.model_validate(data, context={"ctx": ctx})

    @typing_extensions.deprecated(
        "This method is deprecated; use `rest.search` instead."
    )
    async def search(
        self,
        query: str,
        *,
        ctx: Optional[Union[commands.Context, Interaction]] = None,
        requester: Optional[Union[Member, User, ClientUser]] = None,
        search_type: SearchType = SearchType.ytmsearch,
        filters: Optional[List[Filter]] = None,
    ) -> Optional[Union[Playlist, List[Track]]]:
        """Fetches tracks from the node's REST api to parse into Lavalink.

        If you passed in Spotify API credentials, you can also pass in a
        Spotify URL of a playlist, album or track and it will be parsed accordingly.

        You can pass in a disnake Context object to get a
        Context object on any track you search.

        You may also pass in a List of filters
        to be applied to your track once it plays.
        """

        timestamp = None

        if filters:
            for filter in filters:
                filter.set_preload()

        if discord_url := URLRegex.DISCORD_MP3_URL.match(query):
            data: dict = await self.send(
                method="GET",
                path="loadtracks",
                query=f"identifier={quote(query)}",
            )

            track: dict = data["tracks"][0]
            info: dict = track["info"]

            return [
                Track(
                    track_id=track["track"],
                    info={
                        "title": discord_url.group("file"),
                        "author": "Unknown",
                        "length": info["length"],
                        "uri": info["uri"],
                        "position": info["position"],
                        "identifier": info["identifier"],
                    },
                    ctx=ctx,
                    track_type=TrackType.HTTP,
                    filters=filters,
                    requester=requester,
                ),
            ]

        elif path.exists(path.dirname(query)):
            local_file = Path(query)
            data: dict = await self.send(  # type: ignore
                method="GET",
                path="loadtracks",
                query=f"identifier={quote(query)}",
            )

            track: dict = data["tracks"][0]  # type: ignore
            info: dict = track["info"]  # type: ignore

            return [
                Track(
                    track_id=track["track"],
                    info={
                        "title": local_file.name,
                        "author": "Unknown",
                        "length": info["length"],
                        "uri": quote(local_file.as_uri()),
                        "position": info["position"],
                        "identifier": info["identifier"],
                    },
                    ctx=ctx,
                    track_type=TrackType.LOCAL,
                    filters=filters,
                    requester=requester,
                ),
            ]

        else:
            if (
                not URLRegex.BASE_URL.match(query)
                and not URLRegex.LAVALINK_SEARCH.match(query)
                and not URLRegex.LAVALINK_REC.match(query)
            ):
                query = f"{search_type}:{query}"

            # If YouTube url contains a timestamp, capture it for use later.

            if match := URLRegex.YOUTUBE_TIMESTAMP.match(query):
                timestamp = float(match.group("time"))

            data = await self.send(
                method="GET",
                path="loadtracks",
                query=f"identifier={quote(query)}",
            )

        load_type = data.get("loadType")

        # Lavalink v4 changed the name of the key from "tracks" to "data"
        # so lets account for that
        data_type = "data" if self._version.major >= 4 else "tracks"

        if not load_type:
            raise TrackLoadError(
                "There was an error while trying to load this track.",
            )

        elif load_type in ("LOAD_FAILED", "error"):
            exception = data.get("exception", data.get("data"))
            raise TrackLoadError(
                f"{exception['message']} [{exception['severity']}]",
            )

        elif load_type in ("NO_MATCHES", "empty"):
            return None

        elif load_type in ("PLAYLIST_LOADED", "playlist"):
            if self._version.major >= 4:
                track_list = data[data_type]["tracks"]
                playlist_info = data[data_type]["info"]
            else:
                track_list = data[data_type]
                playlist_info = data["playlistInfo"]
            tracks = [
                Track(
                    track_id=track["encoded"],
                    info=track["info"],
                    plugin_info=track["pluginInfo"],
                    ctx=ctx,
                    requester=requester,
                    track_type=TrackType(track["info"]["sourceName"]),
                )
                for track in track_list
            ]
            return Playlist(
                playlist_info=playlist_info,
                tracks=tracks,
                playlist_type=PlaylistType(tracks[0].track_type.value),
                thumbnail=tracks[0].thumbnail,
                uri=query,
            )

        elif load_type in ("SEARCH_RESULT", "TRACK_LOADED", "track", "search"):
            if self._version.major >= 4 and isinstance(data[data_type], dict):
                data[data_type] = [data[data_type]]
            return [
                Track(
                    track_id=track["encoded"],
                    info=track["info"],
                    plugin_info=track["pluginInfo"],
                    ctx=ctx,
                    track_type=TrackType(track["info"]["sourceName"]),
                    filters=filters,
                    timestamp=timestamp,
                    requester=requester,
                )
                for track in data[data_type]
            ]

        else:
            raise TrackLoadError(
                "There was an error while trying to load this track.",
            )

    @typing_extensions.deprecated(
        "This method is deprecated; use `rest.get_recommendations` instead."
    )
    async def get_recommendations(
        self,
        *,
        track: Track,
        playlist_id: Optional[str] = None,
        seed_tracks: Optional[str] = None,
        ctx: Optional[Union[commands.Context, Interaction]] = None,
        requester: Optional[Union[Member, User, ClientUser]] = None,
        **kwargs,
    ) -> Optional[Union[List[Track], Playlist]]:
        """
        Gets recommendations from either YouTube or Spotify.
        The track that is passed in must be either from
        YouTube or Spotify or else this will not work.
        You can pass in a disnake Context object to get a
        Context object on all tracks that get recommended.
        """
        if track.track_type == TrackType.SPOTIFY:
            if track and not seed_tracks:
                seed_tracks = track.identifier

            query = f"sprec:seed_tracks={seed_tracks}"

            for param in kwargs:
                query += f"&{param}={kwargs.get(param) if type(kwargs.get(param)) == str else ','.split(kwargs.get(param))}"

            return await self.search(
                query=query, ctx=ctx or track.ctx, requester=requester
            )

        elif track.track_type == TrackType.YOUTUBE:
            if not playlist_id:
                query = self._ytm_client.get_watch_playlist(
                    videoId=track.identifier, **kwargs
                )["tracks"]
            else:
                query = self._ytm_client.get_watch_playlist(
                    playlistId=playlist_id, **kwargs
                )["tracks"]

            tracks = []

            for song in query:
                tracks.append(
                    (
                        await self.search(
                            f"https://music.youtube.com/watch?v={song['videoId']}",
                            ctx=ctx,
                            requester=requester,
                        )
                    )[0]
                )

            return tracks[1:]

        else:
            raise TrackLoadError(
                "The specfied track must be either a YouTube or Spotify track to recieve recommendations.",
            )


class NodePool:
    """The base class for the node pool.
    This holds all the nodes that are to be used by the bot.
    """

    _nodes: Dict[str, Node] = {}

    def __repr__(self) -> str:
        return f"<PersikTunes.NodePool node_count={self.node_count}>"

    @property
    def nodes(self) -> Dict[str, Node]:
        """Property which returns a dict with the node identifier and the Node object."""
        return self._nodes

    @property
    def node_count(self) -> int:
        return len(self._nodes.values())

    @classmethod
    def get_best_node(cls, *, algorithm: NodeAlgorithm) -> Node:
        """Fetches the best node based on an NodeAlgorithm.
        This option is preferred if you want to choose the best node
        from a multi-node setup using either the node's latency
        or the node's voice region.

        Use NodeAlgorithm.by_ping if you want to get the best node
        based on the node's latency.


        Use NodeAlgorithm.by_players if you want to get the best node
        based on how players it has. This method will return a node with
        the least amount of players
        """
        available_nodes: List[Node] = [
            node for node in cls._nodes.values() if node._available
        ]

        if not available_nodes:
            raise NoNodesAvailable("There are no nodes available.")

        if algorithm == NodeAlgorithm.by_ping:
            tested_nodes = {node: node.latency for node in available_nodes}
            return min(tested_nodes, key=tested_nodes.get)  # type: ignore

        elif algorithm == NodeAlgorithm.by_players:
            tested_nodes = {node: len(node.players.keys()) for node in available_nodes}
            return min(tested_nodes, key=tested_nodes.get)  # type: ignore

        else:
            raise ValueError(
                "The algorithm provided is not a valid NodeAlgorithm.",
            )

    @classmethod
    def get_node(cls, *, identifier: Optional[str] = None) -> Node:
        """Fetches a node from the node pool using it's identifier.
        If no identifier is provided, it will choose a node at random.
        """
        available_nodes = {
            identifier: node
            for identifier, node in cls._nodes.items()
            if node._available
        }

        if not available_nodes:
            raise NoNodesAvailable("There are no nodes available.")

        if identifier is None:
            return random.choice(list(available_nodes.values()))

        return available_nodes[identifier]

    @classmethod
    async def create_node(
        cls,
        *,
        bot: commands.Bot,
        host: str,
        port: int,
        password: str,
        identifier: str,
        secure: bool = False,
        heartbeat: int = 120,
        resume_key: Optional[str] = None,
        resume_timeout: int = 60,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        session: Optional[aiohttp.ClientSession] = None,
        fallback: bool = False,
        log_level: LogLevel = LogLevel.INFO,
        log_handler: Optional[logging.Handler] = None,
        spotify_credentials: Optional[SpotifyClientCredentials] = None,
    ) -> Node:
        """Creates a Node object to be then added into the node pool.
        For Spotify searching capabilites, pass in valid Spotify API credentials.
        """
        if identifier in cls._nodes.keys():
            raise NodeCreationError(
                f"A node with identifier '{identifier}' already exists.",
            )

        node = Node(
            pool=cls,
            bot=bot,
            host=host,
            port=port,
            password=password,
            identifier=identifier,
            secure=secure,
            heartbeat=heartbeat,
            resume_key=resume_key,
            resume_timeout=resume_timeout,
            loop=loop,
            session=session,
            fallback=fallback,
            log_level=log_level,
            log_handler=log_handler,
            spotify_credentials=spotify_credentials,
        )

        await node.connect()
        cls._nodes[node._identifier] = node
        return node

    @classmethod
    async def disconnect(cls) -> None:
        """Disconnects all available nodes from the node pool."""

        available_nodes: List[Node] = [
            node for node in cls._nodes.values() if node._available
        ]

        for node in available_nodes:
            await node.disconnect()
