import asyncio
import json
import logging
import random
from typing import Any, Callable, Optional

from disnake.ext import commands
from websockets import client, exceptions

from .. import __version__
from ..enums import LogLevel
from ..models import ws as wsmodels
from ..models.ws import *
from ..utils import ExponentialBackoff, LavalinkVersion


class LavalinkWebsocket:
    """
    Lavalink Websocket class\n
    #### `/v4/websocket`
    """

    def __init__(
        self,
        node: Any,
        host: str,
        port: int,
        password: str,
        user_id: int,
        secure: bool = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        fallback: bool = False,
        get_player: Optional[Callable] = None,
        log_level: LogLevel = LogLevel.INFO,
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
            loop: Optional[asyncio.AbstractEventLoop] - The asyncio event loop.
            fallback: bool - Flag indicating if fallback should be enabled.
            get_player: Optional[Callable] - Optional function to get player.
            log_level: LogLevel - The log level for logging.
            setup_logging: Optional[Callable] - Optional function for setting up logging.
            configure_resuming: Optional[Callable] - Optional function for configuring resuming.

        Returns:
            None
        """

        self._node: Any = node

        self._bot: commands.Bot = node.bot

        self._host: str = host
        self._port: int = port
        self._password: str = password
        self._identifier: str = node._identifier
        self._secure: bool = secure
        self._fallback: bool = fallback

        self._log_level: LogLevel = log_level

        self._websocket_uri: str = (
            f"{'wss' if self._secure else 'ws'}://{self._host}:{self._port}"
        )

        # self._session: aiohttp.ClientSession = session  # type: ignore
        self._loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()
        self._websocket: client.WebSocketClientProtocol
        self._task: asyncio.Task = None  # type: ignore

        self._session_id: Optional[str] = None
        self._version: LavalinkVersion = LavalinkVersion(0, 0, 0)

        self._log = (
            self._node._setup_logging(self._log_level)
            if not setup_logging
            else setup_logging(self._log_level)
        )

        self._configure_resuming = configure_resuming or node._configure_resuming

        self.get_player = get_player or node.get_player

        self.user_id = user_id

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

        op = BaseWebsocketResponse.model_validate(data).op

        if op == "ready":
            self._session_id = ReadyOP.model_validate(data).sessionId
            self._node._session_id = self._session_id
            if self._node._version.major == 4:
                await self._node.set_resume_key(self._session_id)
                await self._configure_resuming()

            return self._node.event.set()

        elif op == "stats":
            self._node._stats = StatsOP.model_validate(data)
            return

        elif op == "event":
            event = getattr(wsmodels, data.get("type")).model_validate(data)
            player = self.get_player(int(event.guildId))
            return await player._dispatch_event(event) if player else None

        elif op == "playerUpdate":
            update = PlayerUpdateOP.model_validate(data)
            player = self.get_player(int(update.guildId))
            return await player._update_state(update) if player else None

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
                if self._node.player_count > 0 and not self._node._get_resume_key:
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
