from typing import Any, Dict, Optional

from ..enums import URLRegex, YoutubeIdMatchingRegex
from ..models import Album, Artist, Playlist, Track
from .spotify import *
from .template import BaseSearch
from .yandexmusic import *
from .youtubemusic import *


class AbstractSearch(BaseSearch):
    """
    #### Abstract class for search functions.
    You can use this class to search from many services from here.
    """

    def __init__(
        self,
        node: Any,
        default: Union[BaseSearch, YoutubeMusicSearch] = YoutubeMusicSearch,
        **kwargs,
    ) -> None:
        """Pass a `Node` instance and get started.\nYou can pass any additional kwarg: `language`"""

        self.node = node

        self.youtube = YoutubeMusicSearch(node, **kwargs)

        self.default = default(node, **kwargs)

    async def _call_method(
        self, method_name: str, obj: Any | None = None, *args, **kwargs
    ) -> Any | None:

        if isinstance(obj, Track) or not obj:
            if method_name == "ongoing":
                return getattr(self.default, method_name)(obj, *args, **kwargs)

            return await getattr(self.default, method_name)(obj, *args, **kwargs)

        elif isinstance(obj, str):
            if method_name == "search_suggestions":
                return await getattr(self.default, method_name)(obj, *args, **kwargs)

            if URLRegex.YOUTUBE_URL.match(obj):
                if query := YoutubeIdMatchingRegex.SONG.findall(obj):
                    id = query[0]

                    return await self.youtube.song(id, *args, **kwargs)
                elif query := YoutubeIdMatchingRegex.PLAYLIST.findall(obj):
                    id = query[0]

                    return await self.youtube.playlist(id, *args, **kwargs)

                return await getattr(self.youtube, method_name)(query, *args, **kwargs)

            elif URLRegex.BASE_URL.match(obj):
                return await self.node.rest.search(
                    obj, ctx=kwargs.get("ctx"), requester=kwargs.get("requester")
                )

            else:
                return await self.default.search_songs(obj, *args, **kwargs)

    async def search_songs(
        self, query: str, limit: int = 10, *args, **kwargs
    ) -> Optional[List[Track]] | Any:
        """Search for songs"""
        return await self._call_method(
            "search_songs", query, limit=limit, *args, **kwargs
        )

    async def search_albums(
        self, query: str, limit: int = 10, *args, **kwargs
    ) -> Optional[List[Album]] | Any:
        """Search for albums"""
        return await self._call_method(
            "search_albums", query, limit=limit, *args, **kwargs
        )

    async def search_playlists(
        self, query: str, limit: int = 10, *args, **kwargs
    ) -> Optional[List[Playlist]] | Any:
        """Search for playlists"""
        return await self._call_method(
            "search_playlists", query, *args, limit=limit, **kwargs
        )

    async def search_artists(
        self, query: str, *args, **kwargs
    ) -> Optional[List[Artist]] | Any:
        """Search for artists"""
        return await self._call_method("search_artists", query, *args, **kwargs)

    async def search_suggestions(
        self, query: str, *args, **kwargs
    ) -> Optional[Dict[str, str]] | Any:
        """Autocomplete your search from default service"""
        return await self._call_method("search_suggestions", query, *args, **kwargs)

    async def search(
        self, query: str, limit: int = 1, *args, **kwargs
    ) -> Optional[List[Track]] | Any:
        """Legacy provider for search_songs"""
        return await self.search_songs(query, limit=limit, *args, **kwargs)

    async def song(self, id: str, *args, **kwargs) -> Optional[Track]:
        """Get song by id"""
        return await self._call_method("song", id, *args, **kwargs)

    async def album(self, id: str, *args, **kwargs) -> Optional[Album]:
        """Get album by id"""
        return await self._call_method("album", id, *args, **kwargs)

    async def playlist(self, id: str, *args, **kwargs) -> Optional[Playlist]:
        """Get playlist by id"""
        return await self._call_method("playlist", id, *args, **kwargs)

    async def artist(self, id: str, *args, **kwargs) -> Optional[Artist]:
        """Get artist by id"""
        return await self._call_method("artist", id, *args, **kwargs)

    async def moods(self, *args, **kwargs) -> Optional[Dict[str, str]]:
        """Get all moods from default service"""
        return await self._call_method("moods", *args, **kwargs)

    async def get_mood_playlists(
        self, mood: Mood, *args, **kwargs
    ) -> Optional[Playlist]:
        """Get mood playlists from default service"""
        return await self._call_method("get_mood_playlists", mood, *args, **kwargs)

    async def lyrics(self, song: Track, *args, **kwargs) -> Optional[Track]:
        """Get lyrics for song (using path model)"""
        return await self._call_method("lyrics", song, *args, **kwargs)

    async def related(
        self, song: Track, limit: int = 10, *args, **kwargs
    ) -> Optional[List[Track]]:
        """Get related songs for song"""
        return await self._call_method("related", song, limit, *args, **kwargs)

    async def ongoing(
        self, song: Track, limit: int = 40, *args, **kwargs
    ) -> AsyncGenerator[Track, None]:
        """Generate ongoing playlist for song"""
        return await self._call_method("ongoing", song, limit, *args, **kwargs)
