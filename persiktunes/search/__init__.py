"""
### Search module `main`

This module contains all the search functions used in PersikTunes.
"""

from ..models import Playlist, Track


class BaseSearch:
    """Search class template"""

    def get_recommendations(
        self,
        track: Track = None,
        tracks: List[Track] = None,
        playlist: Track = None,
        *args,
        **kwargs
    ) -> Any:
        raise NotImplementedError

    def get_genres(self) -> Any:
        raise NotImplementedError

    def get_relayted_playlists(self, playlist: Playlist, *args, **kwargs) -> Any:
        raise NotImplementedError

    def search(self, query: str, filter: str = None, *args, **kwargs) -> Any:
        raise NotImplementedError

    def get_albums(self, query: str, *args, **kwargs) -> Any:
        raise NotImplementedError

    def get_artists(self, query: str, *args, **kwargs) -> Any:
        raise NotImplementedError


from .builtin import *
from .spotify import *
from .yandexmusic import *
from .youtubemusic import *
