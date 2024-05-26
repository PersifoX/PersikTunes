"""
### Player module `main`

This module contains all the player used in PersikTunes.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Union

from disnake import Client, Guild, VoiceChannel, VoiceProtocol

from . import events
from .exceptions import TrackInvalidPosition
from .filters import Filter, Filters, Timescale

# from .objects import Playlist, Track
from .models import PlayerUpdateOP, Track, UpdatePlayerRequest, UpdatePlayerTrack
from .models.restapi import LavalinkPlayer
from .models.ws import *
from .pool import Node, NodePool
from .utils import LavalinkVersion


class Player(VoiceProtocol):
    """The base player class for PersikTunes.\n
    In order to initiate a player, you must pass it in as a cls when you connect to a channel.\n
    i.e:

    ```py
    await ctx.author.voice.channel.connect(cls=persiktunes.Player)
    ```
    Or use `connect` function:

    ```py
    player = persiktunes.Player(
        client,
        ctx.author.voice.channel
    )

    await player.connect()
    ```
    """

    def __call__(self, client: Client, channel: VoiceChannel) -> Player:
        self.client = client
        self.channel = channel
        self._guild = channel.guild

        return self

    def __init__(
        self,
        client: Client,
        channel: VoiceChannel,
        *,
        node: Optional[Node] = None,
    ) -> None:
        self.client: Client = client
        self.channel: VoiceChannel = channel
        self._guild = channel.guild

        self._guild_id = self._guild.id

        self._bot: Client = client
        self._node: Node = node if node else NodePool.get_node()
        self._current: Optional[Track] = None
        self._filters: Filters = Filters()
        self._volume: int = 100
        self._paused: bool = False
        self._is_connected: bool = False

        self._last_position: int = 0
        self._last_update: float = 0
        self._log = self._node._log

        self._voice_state: dict = {}

        self._player_endpoint_uri: str = f"sessions/{self._node._session_id}/players"

        self.rest = self._node.rest

        self.search = self.rest.search
        self.recommendations = self.rest.recommendations
        self.decode_track = self.rest.decode_track
        self.decode_tracks = self.rest.decode_tracks

    async def from_model(self, model: LavalinkPlayer) -> Player:
        self._current = model.track
        self._volume = model.volume
        self._paused = model.paused

        self._last_position = model.state.position
        self._is_connected = model.state.connected
        self._ping = model.state.ping
        self._last_update = model.state.time

        self._guild_id = model.guildId

        self._voice_state = {
            "event": {"token": model.voice.token, "endpoint": model.voice.endpoint},
            "sessionId": model.voice.sessionId,
        }

        self._log.debug(
            f"Created player from LavalinkPlayer model {model.model_dump()}, connecting..."
        )

        await self.connect(timeout=0, reconnect=True)

        return self

    def __repr__(self) -> str:
        return (
            f"<PersikTunes.player bot={self.bot} guildId={self.guild.id} "
            f"is_connected={self.is_connected} is_playing={self.is_playing}>"
        )

    @property
    def position(self) -> float:
        """Property which returns the player's position in a track in milliseconds"""
        if not self.is_playing:
            return 0

        current: Track = self._current  # type: ignore

        if self.is_paused:
            return min(self._last_position, current.info.length)

        difference = (time.time() * 1000) - self._last_update
        position = self._last_position + difference

        return min(position, current.info.length)

    @property
    def rate(self) -> float:
        """Property which returns the player's current rate"""
        if _filter := next(
            (f for f in self._filters._filters if isinstance(f, Timescale)), None
        ):
            return _filter.speed or _filter.rate
        return 1.0

    @property
    def adjusted_position(self) -> float:
        """Property which returns the player's position in a track in milliseconds adjusted for rate"""
        return self.position / self.rate

    @property
    def adjusted_length(self) -> float:
        """Property which returns the player's track length in milliseconds adjusted for rate"""
        if not self.is_playing:
            return 0

        return self.current.info.length / self.rate  # type: ignore

    @property
    def is_playing(self) -> bool:
        """Property which returns whether or not the player is actively playing a track."""
        return self._is_connected and self._current

    @property
    def is_connected(self) -> bool:
        """Property which returns whether or not the player is connected"""
        return self._is_connected

    @property
    def is_paused(self) -> bool:
        """Property which returns whether or not the player has a track which is paused or not."""
        return self._is_connected and self._paused

    @property
    def current(self) -> Optional[Track]:
        """Property which returns the currently playing track"""
        return self._current

    @property
    def node(self) -> Node:
        """Property which returns the node the player is connected to"""
        return self._node

    @property
    def guild(self) -> Guild:
        """Property which returns the guild associated with the player"""
        return self._guild

    @property
    def volume(self) -> int:
        """Property which returns the players current volume"""
        return self._volume

    @property
    def filters(self) -> Filters:
        """Property which returns the helper class for interacting with filters"""
        return self._filters

    @property
    def bot(self) -> Client:
        """Property which returns the bot associated with this player instance"""
        return self._bot

    @property
    def is_dead(self) -> bool:
        """Returns a bool representing whether the player is dead or not.
        A player is considered dead if it has been destroyed and removed from stored players.
        """
        return self.guild.id not in self._node._players

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Private methods

    def _adjust_end_time(self) -> Optional[str]:
        if self._node._version >= LavalinkVersion(3, 7, 5):
            return None

        return "0"

    async def _update_state(self, data: PlayerUpdateOP) -> None:
        self._last_update = data.state.time
        self._is_connected = data.state.connected or self._is_connected
        self._last_position = data.state.position
        self._ping = data.state.ping
        self._log.debug(
            f"Got player update state with PlayerUpdateOP {data.model_dump()}"
        )

    async def _dispatch_voice_update(
        self, voice_data: Optional[Dict[str, Any]] = None
    ) -> None:

        state = voice_data or self._voice_state

        data = (
            {
                "token": state["event"]["token"],
                "endpoint": state["event"]["endpoint"],
                "sessionId": state["sessionId"],
            }
            if state
            else None
        )

        await self.rest.update_player(
            guild_id=self._guild.id,
            data={"voice": data},
        )

        self._log.debug(
            f"Dispatched voice update to {state['event']['endpoint']} with data {data}"
        )

    async def on_voice_server_update(self, data: Any) -> None:
        self._voice_state.update({"event": data})
        await self._dispatch_voice_update(self._voice_state)

    async def on_voice_state_update(self, data: Any) -> None:
        self._voice_state.update({"sessionId": data.get("session_id")})

        channel_id = data.get("channel_id")
        if not channel_id:
            await self.disconnect()
            self._voice_state.clear()
            return

        channel = self.guild.get_channel(int(channel_id))
        if not channel:
            await self.disconnect()
            self._voice_state.clear()
            return

        if not data.get("token"):
            return

        await self._dispatch_voice_update({**self._voice_state, "event": data})

    async def _dispatch_event(
        self,
        event: Union[
            TrackEndEvent,
            TrackStartEvent,
            TrackStuckEvent,
            TrackExceptionEvent,
            WebSocketClosedEvent,
            Any,
        ],
    ) -> None:
        event_type: str = event.__class__.__name__
        ds_event: events.PersikEvent = getattr(events, event_type)(
            event.model_dump(), self
        )

        if isinstance(event, TrackEndEvent) and event.reason != "replaced":
            self._current = None

        ds_event.dispatch(self._bot)

        self._log.debug(f"Dispatched event {event_type} ({ds_event}) to player.")

    async def _refresh_endpoint_uri(self, session_id: Optional[str]) -> None:
        self._player_endpoint_uri = f"sessions/{session_id}/players"

    async def _swap_node(self, *, new_node: Node) -> None:
        if self.current:
            data: dict = {
                "position": self.position,
                "encodedTrack": self.current.encoded,
            }

        del self._node._players[self._guild.id]
        self._node = new_node
        self._node._players[self._guild.id] = self
        # reassign uri to update session id
        await self._refresh_endpoint_uri(new_node._session_id)
        await self._dispatch_voice_update()
        await self.rest.update_player(
            guild_id=self._guild.id,
            data=data or {},
        )

        self._log.debug(f"Swapped all players to new node {new_node._identifier}.")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Public methods

    async def connect(
        self,
        *,
        timeout: float,
        reconnect: bool,
        self_deaf: bool = True,
        self_mute: bool = False,
    ) -> None:
        await self.guild.change_voice_state(
            channel=self.channel,
            self_deaf=self_deaf,
            self_mute=self_mute,
        )

        self._node._players[self.guild.id] = self
        self._is_connected = True

        await self.node.set_player_channel(self, self.channel.id)

        self._log.debug(
            f"Connected to voice channel {self.channel} in guild {self.guild}."
        )

    async def stop(self) -> None:
        """Stops the currently playing track."""
        self._current = None
        await self.rest.update_player(
            guild_id=self._guild.id,
            data={"encodedTrack": None},
        )

        self._log.debug(f"Player has been stopped.")

    async def disconnect(self, *, force: bool = False) -> None:
        """Disconnects the player from voice."""
        try:
            await self.guild.change_voice_state(channel=None)
            await self.node.set_player_channel(self, None)
        finally:
            self.cleanup()
            self._is_connected = False
            self.channel = None  # type: ignore

    async def destroy(self) -> None:
        """Disconnects and destroys the player, and runs internal cleanup."""
        try:
            await self.disconnect()
        except AttributeError:
            # 'NoneType' has no attribute '_get_voice_client_key' raised by self.cleanup() ->
            # assume we're already disconnected and cleaned up
            assert self.channel is None and not self.is_connected

        self._node._players.pop(self.guild.id)
        if self.node.is_connected:
            await self.rest.destroy_player(guild_id=self._guild.id)

        self._log.debug("Player has been destroyed.")

    async def play(
        self,
        track: Track,
        *,
        start: int = 0,
        end: Optional[int] = None,
        noReplace: bool = True,
        volume: Optional[int] = None,
    ) -> Track:
        """Plays a track"""

        data = UpdatePlayerRequest(  # NOTE: Cannot specify both encodedTrack and identifier, we passed encoded here
            noReplase=noReplace,
            track=UpdatePlayerTrack(
                encoded=track.encoded,
                userData=track,
            ),
            position=start or 0,
            endTime=end or None,
            volume=volume or self.volume,
            pause=False,
        )

        self._paused = False

        # Lets set the current track before we play it so any
        # corresponding events can capture it correctly

        self._current = track

        # Remove preloaded filters if last track had any
        if self.filters.has_preload:
            for filter in self.filters.get_preload_filters():
                await self.remove_filter(filter_tag=filter.tag)

        # Global filters take precedence over track filters
        # So if no global filters are detected, lets apply any
        # necessary track filters

        # Check if theres no global filters and if the track has any filters
        # that need to be applied

        if track.filters and not self.filters.has_global:
            # Now apply all filters
            for filter in track.filters:
                await self.add_filter(_filter=filter)

        # Lavalink v3.7.5 changed the way the end time parameter works
        # so now the end time cannot be zero.
        # If it isnt zero, it'll be set to None.
        # Otherwise, it'll be set here:

        await self.rest.update_player(guild_id=self._guild.id, data=data)

        self._log.debug(
            f"Playing {track.info.title} from uri {track.info.uri} with a length of {track.info.length}",
        )

        return self._current

    async def seek(self, position: int) -> int:
        """Seeks to a position in the currently playing track milliseconds"""
        if not self._current or not self._current.encoded:
            return 0.0

        if position < 0 or position > self._current.info.length:
            raise TrackInvalidPosition(
                "Seek position must be between 0 and the track length",
            )

        await self.rest.update_player(
            guild_id=self._guild.id,
            data={"position": int(position)},
        )

        self._log.debug(f"Seeking to {position}.")
        return self.position

    async def set_pause(self, pause: Optional[bool] = None) -> bool:
        """Sets the pause state of the currently playing track."""
        await self.rest.update_player(
            guild_id=self._guild.id,
            data={"paused": pause or not self._paused},
        )

        self._paused = pause or not self._paused

        self._log.debug(
            f"Player has been {'paused' if self._paused else 'resumed'}. ({pause or not self._paused})"
        )
        return self._paused

    async def set_volume(self, volume: int) -> int:
        """Sets the volume of the player as an integer. Lavalink accepts values from 0 to 500."""

        await self.rest.update_player(guild_id=self._guild.id, data={"volume": volume})

        self._volume = volume

        self._log.debug(f"Player volume has been adjusted to {volume}")
        return self._volume

    async def move_to(self, channel: VoiceChannel) -> None:
        """Moves the player to a new voice channel."""

        await self.guild.change_voice_state(channel=channel)

        self._voice_state["channel_id"] = channel.id

        self.channel = channel

        await self._dispatch_voice_update()

    async def add_filter(self, _filter: Filter) -> Filters:
        """Adds a filter to the player. Takes a PersikTunes.Filter object.
        This will only work if you are using a version of Lavalink that supports filters.
        If you would like for the filter to apply instantly, set the `fast_apply` arg to `True`.

        (You must have a song playing in order for `fast_apply` to work.)
        """

        self._filters.add_filter(filter=_filter)

        payload = self._filters.get_all_payloads()

        await self.rest.update_player(
            guild_id=self._guild.id, data={"filters": payload}
        )

        await self.seek(self.position)  # TODO: Find a better way to do this

        self._log.debug(f"Filter has been applied to player with tag {_filter.tag}")

        return self._filters

    async def remove_filter(self, filter_tag: str) -> Filters:
        """Removes a filter from the player. Takes a filter tag.
        This will only work if you are using a version of Lavalink that supports filters.
        If you would like for the filter to apply instantly, set the `fast_apply` arg to `True`.

        (You must have a song playing in order for `fast_apply` to work.)
        """

        self._filters.remove_filter(filter_tag=filter_tag)
        payload = self._filters.get_all_payloads()

        await self.rest.update_player(
            guild_id=self._guild.id, data={"filters": payload}
        )

        await self.seek(self.position)  # TODO: Find a better way to do this

        self._log.debug(f"Filter has been removed from player with tag {filter_tag}")

        return self._filters

    async def edit_filter(self, *, filter_tag: str, edited_filter: Filter) -> Filters:
        """Edits a filter from the player using its filter tag and a new filter of the same type.
        The filter to be replaced must have the same tag as the one you are replacing it with.
        This will only work if you are using a version of Lavalink that supports filters.

        If you would like for the filter to apply instantly, set the `fast_apply` arg to `True`.

        (You must have a song playing in order for `fast_apply` to work.)
        """

        self._filters.edit_filter(filter_tag=filter_tag, to_apply=edited_filter)
        payload = self._filters.get_all_payloads()

        await self.rest.update_player(
            guild_id=self._guild.id, data={"filters": payload}
        )

        await self.seek(self.position)  # TODO: Find a better way to do this

        self._log.debug(
            f"Filter with tag {filter_tag} has been edited to {edited_filter!r}"
        )

        return self._filters

    async def reset_filters(self) -> None:
        """Resets all currently applied filters to their default parameters.
         You must have filters applied in order for this to work.
         If you would like the filters to be removed instantly, set the `fast_apply` arg to `True`.

        (You must have a song playing in order for `fast_apply` to work.)
        """

        if not self._filters:
            # raise FilterInvalidArgument(
            #     "You must have filters applied first in order to use this method.",
            # )
            return self._log.warn(
                "You don't have any filters applied. Nothing to reset."
            )

        self._filters.reset_filters()
        await self.rest.update_player(guild_id=self._guild.id, data={"filters": {}})

        await self.seek(self.position)  # TODO: Find a better way to do this

        self._log.debug(f"All filters have been removed from player.")
