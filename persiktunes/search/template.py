"""Import search template class from here"""

from typing import Dict, List, Optional

from ..models import Album, Artist, Browse, Mood, Playlist, Track


class BaseSearch:
    """Search class template"""

    async def album(self, id: str, *args, **kwargs) -> Optional[Album]:
        raise NotImplementedError

    async def playlist(self, id: str, *args, **kwargs) -> Optional[Playlist]:
        raise NotImplementedError

    async def song(self, id: str, *args, **kwargs) -> Optional[Track]:
        raise NotImplementedError

    async def artist(self, id: str, *args, **kwargs) -> Optional[Artist]:
        raise NotImplementedError

    async def moods(self, *args, **kwargs) -> Optional[List[Mood]]:
        raise NotImplementedError

    async def get_mood_playlists(self, mood: Mood, *args, **kwargs) -> List[Playlist]:
        raise NotImplementedError

    async def search_songs(self, query: str, *args, **kwargs) -> Optional[List[Track]]:
        raise NotImplementedError

    async def search_albums(self, query: str, *args, **kwargs) -> Optional[List[Album]]:
        raise NotImplementedError

    async def search_playlists(
        self, query: str, *args, **kwargs
    ) -> Optional[List[Playlist]]:
        raise NotImplementedError

    async def search_artists(
        self, query: str, *args, **kwargs
    ) -> Optional[List[Artist]]:
        raise NotImplementedError

    async def search_suggestions(
        self, query: str, *args, **kwargs
    ) -> Optional[Dict[str, str]]:
        raise NotImplementedError

    async def relayted(self, song: Track, *args, **kwargs) -> List[Track]:
        raise NotImplementedError

    async def lyrics(self, song: Track, *args, **kwargs) -> Optional[Track]:
        raise NotImplementedError
