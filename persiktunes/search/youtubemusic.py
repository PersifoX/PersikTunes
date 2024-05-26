from typing import Any, AsyncGenerator, List, Union

import ytmusicapi

from services.persiktunes.models import Album, Mood

from ..models import LavalinkPlaylistInfo, LavalinkTrackInfo, Playlist, Track
from .template import BaseSearch


class YoutubeMusicSearch(BaseSearch):
    """
    Youtube Music search abstract class.

    You can use methods without `Node`, just pass context in `kwargs` and go:

    ```py
    from persiktunes import YoutubeMusicSearch
    ...
    search = YoutubeMusicSearch(node = node)
    ...
    @commands.slash_command(description="Play song")
    asyng def play(self, ctx, query: str):
        songs = await search.search_songs(query, ctx=ctx, requester=ctx.author)
        ...
        await player.play(songs[0])
    ```
    """

    def __init__(self, node: Any, **kwargs) -> None:
        """Pass a `Node` instance and get started.\nYou can pass any additional kwarg: `language`"""
        self.client = ytmusicapi.YTMusic(
            auth="data/oauth/oauth.json", language=kwargs.get("language", "ru")
        )
        self.node = node

    async def song(self, id: str, **kwargs) -> Track | None:
        raw = self.client.get_song(id)

        if not raw:
            return None

        raw = raw["videoDetails"]

        info = LavalinkTrackInfo(
            identifier=raw["videoId"],
            isSeekable=True,
            author=raw["author"],
            length=int(int(raw["lengthSeconds"]) * 1000),
            isStream=False,
            position=0,
            title=raw["title"],
            uri=f"https://music.youtube.com/watch?v={raw['videoId']}",
            artworkUrl=raw["thumbnail"]["thumbnails"][0]["url"].split("=")[0],
            sourceName="youtube",
        )

        track = Track(
            encoded=(
                await self.node.rest.send(
                    "GET", f"loadtracks?identifier={raw['videoId']}"
                )
            )["data"]["encoded"],
            info=info,
        )

        return self.node.rest.patch_context(data=track, **kwargs)

    async def album(self, id: str, **kwargs) -> Album | None:
        raw = self.client.get_album(id)

        if not raw:
            return None

        tracks = []

        for rawtrack in raw["tracks"]:

            info = LavalinkTrackInfo(
                identifier=rawtrack["videoId"],
                isSeekable=True,
                author=",".join([artist["name"] for artist in rawtrack["artists"]]),
                length=rawtrack["length"],
                isStream=False,
                position=0,
                title=rawtrack["title"],
                uri=f"https://music.youtube.com/watch?v={rawtrack['videoId']}",
                artworkUrl=(
                    rawtrack["thumbnails"][0]["url"].split("=")[0]
                    if rawtrack["thumbnails"]
                    else None
                ),
                sourceName="youtube",
            )

            tracks.append(
                Track(
                    encoded=(
                        await self.node.rest.send(
                            "GET", f"loadtracks?identifier={rawtrack['videoId']}"
                        )
                    )["data"]["encoded"],
                    info=info,
                    ctx=kwargs.get("ctx"),
                    requester=kwargs.get("requester"),
                    description=rawtrack.get("description"),
                )
            )

        info = LavalinkPlaylistInfo(name=raw["title"], selectedTrack=0)

        album = Album(
            info=info,
            tracks=tracks,
            description=raw.get("description"),
            uri=f"https://music.youtube.com/playlist?list={raw['audioPlaylistId']}",
        )

        return self.node.rest.patch_context(data=album, **kwargs)

    async def playlist(self, id: str, **kwargs) -> Playlist | None:
        raw = self.client.get_playlist(id, limit=500)

        if not raw:
            return None

        tracks = []

        for rawtrack in raw["tracks"]:

            info = LavalinkTrackInfo(
                identifier=rawtrack["videoId"],
                isSeekable=True,
                author=",".join([artist["name"] for artist in rawtrack["artists"]]),
                length=rawtrack["length"],
                isStream=False,
                position=0,
                title=rawtrack["title"],
                uri=f"https://music.youtube.com/watch?v={rawtrack['videoId']}",
                artworkUrl=(
                    rawtrack["thumbnails"][0]["url"].split("=")[0]
                    if rawtrack["thumbnails"]
                    else None
                ),
                sourceName="youtube",
            )

            tracks.append(
                Track(
                    encoded=(
                        await self.node.rest.send(
                            "GET", f"loadtracks?identifier={rawtrack['videoId']}"
                        )
                    )["data"]["encoded"],
                    info=info,
                    ctx=kwargs.get("ctx"),
                    requester=kwargs.get("requester"),
                    description=rawtrack.get("description"),
                )
            )

        info = LavalinkPlaylistInfo(name=raw["title"], selectedTrack=0)

        playlist = Playlist(
            info=info,
            tracks=tracks,
            description=raw.get("description"),
            uri=f"https://music.youtube.com/playlist?list={raw['audioPlaylistId']}",
        )

        return self.node.rest.patch_context(data=playlist, **kwargs)

    async def moods(self, **kwargs) -> List[Mood]:
        raw = self.client.get_mood_categories()

        moods = []

        for name, rawmoods in raw.items():
            for mood in rawmoods:
                moods.append(Mood(title=mood["title"], params=mood["params"]))

        return moods

    async def get_mood_playlists(self, mood: Mood, **kwargs) -> List[Playlist]:
        raw = self.client.get_mood_playlists(mood.params)

        playlists = []

        for rawplaylist in raw:
            playlist = await self.playlist(rawplaylist["playlistId"])
            playlists.append(self.node.rest.patch_context(data=playlist, **kwargs))

        return playlists

    async def search_songs(self, query: str, **kwargs) -> List[Track] | None:
        raw = self.client.search(query, filter="songs")

        if not raw:
            return None

        tracks = []

        for rawresult in raw:
            song = await self.song(rawresult["videoId"], **kwargs)
            tracks.append(song)

        return tracks

    async def search_albums(self, query: str, **kwargs) -> List[Album] | None:
        raw = self.client.search(query, filter="albums")

        if not raw:
            return None

        albums = []

        for rawresult in raw:
            album = await self.album(rawresult["browseId"])
            albums.append(self.node.rest.patch_context(data=album, **kwargs))

        return albums

    async def search_playlists(self, query: str, **kwargs) -> List[Playlist] | None:
        raw = self.client.search(query, filter="playlists")

        if not raw:
            return None

        playlists = []

        for rawresult in raw:
            playlist = await self.playlist(rawresult["browseId"])
            playlists.append(self.node.rest.patch_context(data=playlist, **kwargs))

        return playlists

    async def relayted(
        self, song_or_playlist_id: Union[Track, str], limit: int = 10, **kwargs
    ) -> List[Track]:
        if isinstance(song_or_playlist_id, Track):
            raw = self.client.get_watch_playlist(
                song_or_playlist_id, radio=True, limit=2
            )
        else:
            raw = self.client.get_watch_playlist(
                playlistId=song_or_playlist_id, limit=2
            )

        relayted = self.client.get_song_related(raw["related"])

        tracks = []

        for i, rawtrack in enumerate(relayted[0]["contents"]):
            if i == limit:
                break

            track = await self.song(rawtrack["videoId"], **kwargs)
            tracks.append(track)

        return tracks

    async def ongoing(
        self, song: Track, limit: int = 10, **kwargs
    ) -> AsyncGenerator[Track, None]:
        raw = self.client.get_watch_playlist(
            song.info.identifier, radio=True, limit=limit
        )

        for rawtrack in raw["tracks"][1:]:

            yield await self.song(rawtrack["videoId"], **kwargs)

        return

    async def lyrics(self, song: Track, **kwargs) -> Track | None:
        raw = self.client.get_watch_playlist(song.info.identifier, limit=1)

        if not raw.get("lyrics"):
            return

        lyrics = self.client.get_lyrics(raw["lyrics"]).get("lyrics")

        track = song.model_copy(update={"lyrics": lyrics})

        track = self.node.rest.patch_context(data=track, **kwargs)

        return track

    async def search_suggestions(self, query: str, *args, **kwargs) -> List[str] | None:
        raw = self.client.get_search_suggestions(query)

        return raw
