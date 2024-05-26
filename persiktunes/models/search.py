from typing import List, Optional, Union

from pydantic import BaseModel

from .restapi import Playlist, Track


class Album(Playlist):
    pass


class Artist(BaseModel):
    name: str
    id: str
    tracks: List[Track] = []
    albums: Optional[List[Album]] = None
    singles: Optional[List[Track]] = None
    description: Optional[str] = None
    thumbnail: Optional[str] = None


class Mood(BaseModel):
    title: str
    params: str


class Browse(BaseModel):
    title: str
    contents: List[Union[Playlist, Track, Playlist, Album, Artist, Mood]]
