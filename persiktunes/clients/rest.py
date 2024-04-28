import asyncio
import logging
from typing import Any, Callable, Dict, List, Literal, Optional, Union

import aiohttp
from disnake import Interaction, Member, User
from disnake.ext import commands
from enums import *
from exceptions import NodeNotAvailable, NodeRestException
from models.restapi import *
from models.ws import *
from pool import Node
from utils import LavalinkVersion

from persiktunes import __version__


class LavalinkRest:
    def __init__(
        self,
        *,
        node: Node,
        host: str,
        port: int,
        password: str,
        user_id: int,
        secure: bool = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        session: Optional[aiohttp.ClientSession] = None,
        fallback: bool = False,
        log_level: LogLevel = LogLevel.INFO,
        log_handler: Optional[logging.Handler] = None,
        setup_logging: Optional[Callable] = None,
    ):
        if not isinstance(port, int):
            raise TypeError("Port must be an integer")

        self._host: str = host
        self._port: int = port
        self._password: str = password
        self._fallback: bool = fallback
        self._log_level: LogLevel = log_level
        self._log_handler = log_handler

        self._secure = secure

        self.node = node

        self._session: aiohttp.ClientSession = session  # type: ignore
        self._loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()

        self._session_id: Optional[str] = None
        self._available: bool = False
        self._version: LavalinkVersion = LavalinkVersion(0, 0, 0)

        self._log = (
            self.node._setup_logging(self._log_level)
            if not setup_logging
            else setup_logging(self._log_level)
        )

        self._rest_uri: str = (
            f"{'https' if self._secure else 'http'}://{self._host}:{self._port}"
        )

        self.user_id = user_id

        self._headers = {
            "Authorization": self._password,
            "User-Id": self.user_id,
            "Client-Name": f"PersikTunes/{__version__}",
        }

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

        if not ignore_if_available and not self.node._available:
            raise NodeNotAvailable(
                f"The node '{self.node._identifier}' is unavailable.",
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
            f"Making REST request to Node {self.node._identifier} with method {method} to {uri}",
        )
        if resp.status >= 300:
            resp_data: dict = await resp.json()
            raise NodeRestException(
                f'Error from Node {self.node._identifier} fetching from Lavalink REST api: {resp.status} {resp.reason}: {resp_data["message"]}',
            )

        if method == "DELETE" or resp.status == 204:
            self._log.debug(
                f"REST request to Node {self.node._identifier} with method {method} to {uri} completed sucessfully and returned no data.",
            )
            return await resp.json(content_type=None)

        if resp.content_type == "text/plain":
            self._log.debug(
                f"REST request to Node {self.node._identifier} with method {method} to {uri} completed sucessfully and returned text with body {await resp.text()}",
            )
            return await resp.text()

        self._log.debug(
            f"REST request to Node {self.node._identifier} with method {method} to {uri} completed sucessfully and returned JSON with body {await resp.json()}",
        )
        return await resp.json()

    async def search(
        self,
        query: str,
        *,
        stype: SearchType = SearchType.ytsearch,
        ctx: Optional[Union[commands.Context, Interaction]] = None,
        requester: Optional[Union[Member, User]] = None,
        description: Optional[str] = None,
    ) -> LavalinkTrackLoadingResponse:

        if not re.match(URLRegex.BASE_URL, query):
            query = f"{stype.value}:{query}"

        response = await self.send("GET", f"loadtracks?identifier={query}")

        validated = LavalinkTrackLoadingResponse.model_validate(response)

        typed = type(validated.data)

        if typed == type(List[Track]):
            for track in validated.data:
                track.ctx = ctx
                track.requester = requester
                track.description = description

        elif typed == type(Playlist) or typed == type(Track):
            validated.data.ctx = ctx
            validated.data.requester = requester
            validated.data.description = description

        return validated

    async def decode_track(self, encoded: str) -> LavalinkTrackDecodeResponse:
        response = await self.send("GET", f"decodetrack?encodedTrack={encoded}")
        return LavalinkTrackDecodeResponse.model_validate(response)

    async def decode_tracks(
        self, encoded: List[str]
    ) -> LavalinkTrackDecodeMultiplyResponse:
        response = await self.send("POST", f"decodetracks", data=encoded)
        return LavalinkTrackDecodeMultiplyResponse.model_validate({"tracks": response})

    async def get_players(self) -> List[LavalinkPlayer]:
        response = await self.send("GET", f"sessions/{self._session_id}/players")
        return [LavalinkPlayer.model_validate(player) for player in response]

    async def get_player(self, guild_id: int) -> LavalinkPlayer:
        response = await self.send(
            "GET", f"sessions/{self._session_id}/players/{guild_id}"
        )
        return LavalinkPlayer.model_validate(response)

    async def update_player(
        self, guild_id: int, data: Union[UpdatePlayerRequest, dict]
    ) -> LavalinkPlayer:

        data = (
            data
            if isinstance(data, UpdatePlayerRequest)
            else UpdatePlayerRequest.model_validate(data)
        )

        response = await self.send(
            data.method,
            f"sessions/{self._session_id}/players/{guild_id}",
            data=data.model_dump(exclude=["method", "noReplace"]),
            query=f"noReplace={data.noReplase.__str__().lower()}",
        )

        return LavalinkPlayer.model_validate(response)

    async def destroy_player(self, guild_id: int) -> None:
        await self.send("DELETE", f"sessions/{self._session_id}/players/{guild_id}")

    async def update_session(self, data: Union[UpdateSessionRequest, dict]) -> None:

        data = (
            data
            if isinstance(data, UpdateSessionRequest)
            else UpdateSessionRequest.model_validate(data)
        )

        await self.send(
            data.method,
            f"sessions/{self._session_id}",
            data=data.model_dump(exclude=["method"]),
        )
