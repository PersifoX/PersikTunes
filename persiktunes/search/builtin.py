from typing import Any, Dict, List, Literal

import spotipy
import ytmusicapi


class BuiltIn:
    def __init__(self, **kwargs) -> None:

        self.spotify = spotipy.Spotify(
            client_credentials_manager=kwargs.get("spotify_credentials")
        )
        self.ytmusic = ytmusicapi.YTMusic(language=kwargs.get("language", "ru"))

    def get_recommendations(
        self, type: Literal["yt", "sp"], *args, **kwargs
    ) -> List[Dict[str, str]]:
        """
        A function that gets recommendations based on the type of service provided (YouTube or Spotify), with optional arguments and keyword arguments, and returns a list of dictionaries containing the recommendations.
        """

        if type == "yt":
            result = self.ytmusic.get_song_related(*args, **kwargs)[0]["contents"]

        else:
            result = self.spotify.recommendations(*args, **kwargs)

        return result

    def get_relayted_playlists(
        self, type: Literal["yt", "sp"], id: str
    ) -> List[Dict[str, str]]:
        """
        Get related playlists based on the type (YouTube or Spotify) and the ID.

        Args:
            type (Literal['yt', 'sp']): The type of service (YouTube or Spotify).
            id (str): The ID of the playlist or song.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing information about the related playlists or songs.
        """

        if type == "yt":
            result = self.ytmusic.get_song_related(id)[1]["contents"]

        else:
            result = self.spotify.search(q=f"playlist:{id}", type="playlist")[
                "playlists"
            ]["items"]

        return result

    def get_playlist(self, type: Literal["yt", "sp"], query: str) -> Dict[str, str]:
        """
        Get playlist based on type and query.

        :type: The type of playlist, either 'yt' for YouTube or 'sp' for Spotify.
        :param query: The search query for the playlist.
        :return: A dictionary containing the playlist information.
        """

        if type == "yt":
            playlists, result = self.ytmusic.search(query, filter="playlist"), []

            for i in playlists:
                if i.get("resultType") == "playlist":
                    result.append(
                        self.ytmusic.get_playlist(i.get("playlistId"), limit=500)
                    )

        else:
            result = self.spotify.search(q=query, type="playlist")["playlists"]["items"]

        return result

    def get_genres(self, type: Literal["yt", "sp"]) -> List[Dict[str, str]]:
        """
        Retrieve genres based on the type provided.

        Args:
            type (Literal['yt', 'sp']): The type of service for which to retrieve genres.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing genre information.
        """

        if type == "yt":
            result = list(self.ytmusic.get_mood_categories().values())

        else:
            result = self.spotify.recommendation_genre_seeds()

        return result

    def get_mixes(
        self, type: Literal["yt", "sp"], genre: str | None = None
    ) -> List[Dict[str, str]] | Any | None:
        """
        Retrieves mixes based on the specified type and genre.

        Args:
            type (Literal['yt', 'sp']): The type of music service to retrieve mixes from.
            genre (str): The genre of music to use as a filter for the mixes.

        Returns:
            List[Dict[str, str]] | Any: A list of dictionaries representing the mixes, or any type if an error occurs.
        """

        if type == "yt":
            result = self.ytmusic.get_mood_playlists(genre) if genre else None

        else:
            result = self.spotify.recommendations(seed_genres=[genre] or None)

        return result

    def search(self, type: Literal["yt", "sp"], query: str) -> List[Dict[str, str]]:
        """
        A function to get tracks based on the type and query.

        :param type: Literal['yt', 'sp'], the type of the music service
        :param query: str, the search query
        :return: List[Dict[str, str]], a list of dictionaries containing track information
        """

        if type == "yt":
            result = self.ytmusic.search(query, filter="video")

        else:
            result = self.spotify.search(q=query, type="track")["tracks"]["items"]

        return result
