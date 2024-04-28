import asyncio
import json
import logging
import random
import time
from typing import Callable, Optional, Type

import aiohttp
from disnake.ext import commands
from enums import LogLevel
from exceptions import NodeConnectionFailure
from models.ws import *
from pool import Node
from utils import ExponentialBackoff, LavalinkVersion
from websockets import client, exceptions

from persiktunes import __version__


class LavalinkWebsocket:
    """
    Lavalink Websocket class\n
    #### `/v4/websocket`
    """

    def __init__(
        self,
        *,
        node: Type[Node],
        host: str,
        port: int,
        password: str,
        user_id: int,
        secure: bool = False,
        heartbeat: int = 120,
        resume_key: Optional[str] = None,
        resume_timeout: int = 60,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        fallback: bool = False,
        get_player: Optional[Callable] = None,
        log_level: LogLevel = LogLevel.INFO,
        log_handler: Optional[logging.Handler] = None,
        setup_logging: Optional[Callable] = None,
        configure_resuming: Optional[Callable] = None,
    ) -> None:
        """
        Initialize the LavalinkWebsocket class.

        Parameters:
            node: Type[Node] - The type of Node to be used.
            host: str - The host address of the Lavalink server.
            port: int - The port of the Lavalink server.
            password: str - The password for the Lavalink server.
            user_id: int - The user ID for the Lavalink server.
            secure: bool - Flag indicating if the connection should be secure.
            heartbeat: int - The heartbeat interval in seconds.
            resume_key: Optional[str] - The resume key for resuming sessions.
            resume_timeout: int - The timeout for resuming in seconds.
            loop: Optional[asyncio.AbstractEventLoop] - The asyncio event loop.
            session: Optional[aiohttp.ClientSession] - The aiohttp session.
            fallback: bool - Flag indicating if fallback should be enabled.
            get_player: Optional[Callable] - Optional function to get player.
            log_level: LogLevel - The log level for logging.
            log_handler: Optional[logging.Handler] - Optional logging handler.
            setup_logging: Optional[Callable] - Optional function for setting up logging.
            configure_resuming: Optional[Callable] - Optional function for configuring resuming.

        Returns:
            None
        """

        self._node: Type[Node] = node

        self._bot: commands.Bot = node.bot

        self._host: str = host
        self._port: int = port
        self._password: str = password
        self._identifier: str = node._identifier
        self._heartbeat: int = heartbeat
        self._resume_key: Optional[str] = resume_key
        self._resume_timeout: int = resume_timeout
        self._secure: bool = secure
        self._fallback: bool = fallback

        self._log_level: LogLevel = log_level
        self._log_handler: Optional[logging.Handler] = log_handler

        self._websocket_uri: str = (
            f"{'wss' if self._secure else 'ws'}://{self._host}:{self._port}"
        )

        self._loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()
        self._websocket: client.WebSocketClientProtocol
        self._task: asyncio.Task = None  # type: ignore

        self._session_id: Optional[str] = None
        self._available: bool = False
        self._version: LavalinkVersion = LavalinkVersion(0, 0, 0)

        self._log = (
            self._node._setup_logging(self._log_level)
            if not setup_logging
            else setup_logging(self._log_level)
        )

        self._configure_resuming = configure_resuming or node._configure_resuming

        self.get_player = get_player or node.get_player

        self.user_id = user_id

        self._headers = {
            "Authorization": self._password,
            "User-Id": self.user_id,
            "Client-Name": f"PersikTunes/{__version__}",
        }

        self._bot.add_listener(self._update_handler, "on_socket_response")

    @property
    def is_connected(self) -> bool:
        """Property which returns whether this node is connected or not"""
        return self._websocket is not None and not self._websocket.closed

    async def _update_handler(self, data: dict) -> None:
        await self._bot.wait_until_ready()

        try:
            event = DiscordEvent.model_validate(data)

            if event.t == "VOICE_SERVER_UPDATE":
                guild_id = int(event.d.get("guild_id"))
                try:
                    player = self.get_player(guild_id)
                    await player.on_voice_server_update(event.d)
                except KeyError:
                    return

            elif event.t == "VOICE_STATE_UPDATE":
                if int(event.d.get("user_id")) != self.user_id:
                    return

                guild_id = int(event.d.get("guild_id"))
                try:
                    player = self._node._players[guild_id]
                    await player.on_voice_state_update(event.d)
                except KeyError:
                    return

        except:
            self._log.warning(f"Failed to handle event {data.get('t')}: {data}")

    async def _handle_ws_msg(self, data: dict) -> None:
        self._log.debug(
            f"Recieved raw payload from Node {self._identifier} with data {data}"
        )

        op = BaseWebsocketRequest.model_validate(data).op

        if op == "ready":
            self._session_id = ReadyOP.model_validate(data).sessionId
            return await self._configure_resuming()

        elif op == "stats":
            self._stats = StatsOP.model_validate(data)
            return

        elif op == "event":
            event = EventOP.model_validate(data)
            player = self.get_player(event.guildId)
            return await player._dispatch_event(event)

        elif op == "playerUpdate":
            update = PlayerUpdateOP.model_validate(data)
            player = self.get_player(update.guildId)
            return await player._dispatch_event(event)

    async def _handle_node_switch(self) -> None:
        nodes = [
            node for node in self._node.pool._nodes.copy().values() if node.is_connected
        ]
        new_node = random.choice(nodes)

        for player in self._node.players.copy().values():
            await player._swap_node(new_node=new_node)

        await self.disconnect()

    async def _listen(self) -> None:
        while True:
            try:
                msg = await self._websocket.recv()
                data = json.loads(msg)
                self._log.debug(f"Recieved raw websocket message {msg}")
                self._loop.create_task(self._handle_ws_msg(data=data))
            except exceptions.ConnectionClosed:
                if self._node.player_count > 0:
                    for _player in self._node.players.values():
                        self._loop.create_task(_player.destroy())

                if self._fallback:
                    self._loop.create_task(self._handle_node_switch())

                self._loop.create_task(self._websocket.close())

                backoff = ExponentialBackoff(base=7)
                retry = backoff.delay()
                self._log.debug(
                    f"Retrying connection to Node {self._identifier} in {retry} secs"
                )
                await asyncio.sleep(retry)

                if not self.is_connected:
                    self._loop.create_task(self.connect(reconnect=True))

    async def connect(self, *, reconnect: bool = False):
        """Initiates a connection with a Lavalink node and adds it to the node pool."""
        await self._bot.wait_until_ready()

        start = time.perf_counter()

        if not self._session:
            self._session = aiohttp.ClientSession()

        try:
            if not reconnect:
                version: str = await self._node.send(
                    method="GET",
                    path="version",
                    ignore_if_available=True,
                    include_version=False,
                )

                await self._node._handle_version_check(version=version)

                self._log.debug(
                    f"Version check from Node {self._identifier} successful. Returned version {version}",
                )

            self._websocket = await client.connect(
                f"{self._websocket_uri}/v{self._version.major}/websocket",
                extra_headers=self._headers,
                ping_interval=self._heartbeat,
            )

            if reconnect:
                self._log.debug(f"Trying to reconnect to Node {self._identifier}...")
                if self._node.player_count:
                    for player in self._node.players.values():
                        await player._refresh_endpoint_uri(self._session_id)

            self._log.debug(
                f"Node {self._identifier} successfully connected to websocket using {self._websocket_uri}/v{self._version.major}/websocket",
            )

            if not self._task:
                self._task = self._loop.create_task(self._listen())

            self._available = True

            end = time.perf_counter()

            self._log.info(
                f"Connected to node {self._identifier}. Took {end - start:.3f}s"
            )
            return self

        except (aiohttp.ClientConnectorError, OSError, ConnectionRefusedError):
            raise NodeConnectionFailure(
                f"The connection to node '{self._identifier}' failed.",
            ) from None
        except exceptions.InvalidHandshake:
            raise NodeConnectionFailure(
                f"The password for node '{self._identifier}' is invalid.",
            ) from None
        except exceptions.InvalidURI:
            raise NodeConnectionFailure(
                f"The URI for node '{self._identifier}' is invalid.",
            ) from None

    async def disconnect(self, fall: bool = False) -> None:
        """Disconnects a connected Lavalink node and removes it from the node pool.
        This also destroys any players connected to the node.
        """

        if fall:
            self._log.error("Failed to connect to Lavalink node.")

        start = time.perf_counter()

        for player in self._node.players.copy().values():
            await player.destroy()
            self._log.debug("All players disconnected from node.")

        await self._websocket.close()
        await self._session.close()
        self._log.debug("Websocket and http session closed.")

        del self._node.pool._nodes[self._identifier]
        self._available = False
        self._task.cancel()

        end = time.perf_counter()
        self._log.info(
            f"Successfully disconnected from node {self._identifier} and closed all sessions. Took {end - start:.3f}s",
        )
