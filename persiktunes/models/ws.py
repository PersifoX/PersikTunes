from typing import Literal, Optional

from pydantic import BaseModel

from .restapi import LavalinkExceptionResponse, Track

"""
LAVALINK WS MODELS
"""


class BaseWebsocketRequest(BaseModel):
    op: Literal["ready", "playerUpdate", "event", "stats"]


class PlayerState(BaseModel):
    time: int
    position: int
    connected: bool
    ping: int


class Memory(BaseModel):
    free: int
    used: int
    allocated: int
    reservable: int


class Cpu(BaseModel):
    cores: int
    systemLoad: float
    lavalinkLoad: float


class FrameStats(BaseModel):
    sent: int
    nulled: int
    deflict: Optional[int] = None


class ReadyOP(BaseWebsocketRequest):
    resumed: bool
    sessionId: str


class PlayerUpdateOP(BaseWebsocketRequest):
    guildId: str
    state: PlayerState


class StatsOP(BaseWebsocketRequest):
    players: int
    playingPlayers: int
    uptime: int
    memory: Memory
    cpu: Cpu
    frameStats: Optional[FrameStats] = None


class EventOP(BaseWebsocketRequest):
    type: Literal[
        "TrackStartEvent",
        "TrackEndEvent",
        "TrackStuckEvent",
        "TrackExceptionEvent",
        "WebSocketClosedEvent",
    ]
    guildId: str


class TrackStartEvent(EventOP):
    track: Track


class TrackEndEvent(EventOP):
    track: Track
    reason: Literal["finished", "loadFailed", "stopped", "replaced", "cleanup"]


class TrackExceptionEvent(EventOP):
    track: Track
    exception: LavalinkExceptionResponse


class TrackStuckEvent(EventOP):
    track: Track
    threshold: int


class WebSocketClosedEvent(EventOP):
    code: int
    reason: str
    byRemote: bool


"""
DISCORD API MODELS
"""


class DiscordEvent(BaseModel):
    t: Literal[
        "VOICE_SERVER_UPDATE",
        "VOICE_STATE_UPDATE",
    ]

    d: dict
