import time
from urllib.request import urlopen
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth


REDIRECT_URI: str = 'http://127.0.0.1:5000/redirect'
APPLICATION_SCOPE: str = 'playlist-modify-private playlist-modify-public'  # Permissions required to run application.
APPLE_MUSIC_SONG_DIV_CLASS: str = 'songs-list-row__song-name'  # Used to find the song name during scraping.
APPLE_MUSIC_PLAYLIST_TITLE_H1_CLASS: str = 'headings__title'  # Used to find the name of the Apple Music playlist.
ARTIST_ROW_DIV_CLASS: str = 'songs-list-row__by-line'  # Used to find artist during scraping.
CONVERTED_PLAYLIST_DESCRIPTION: str = 'Playlist converted from Apple Music.'  # Spotify playlist description.
PLAYLIST_ITEM_ADD_LIMIT: int = 100  # Spotify's limit to the number of songs you can add to a playlist per request.
QUERY_SLEEP_TIME_SEC: float = 0.5  # Slows down searches to prevent reaching the API quota.


def scrape_apple_music_webpage(url: str) -> [str, list[[str, str]]]:
    # Obtain the playlist HTML page.
    page = urlopen(url)
    html = page.read().decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    playlist_name: str = soup.find('h1', class_=APPLE_MUSIC_PLAYLIST_TITLE_H1_CLASS).text

    # Look for the songs listed on the page.
    songs: list[str] = []
    for element in soup.find_all('div', class_=APPLE_MUSIC_SONG_DIV_CLASS):
        songs.append(element.text)

    # Look for the artists.
    artists: list[str] = []
    for element in soup.find_all('div', class_=ARTIST_ROW_DIV_CLASS):
        artists.append(element.find('a').text)  # Each artist name is a link on the page.

    return playlist_name, list(zip(songs, artists))


def convert_apple_music_playlist(apple_playlist_url: str, public: bool = False) -> str:
    playlist_name, tuples = scrape_apple_music_webpage(apple_playlist_url)
    spot = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope=APPLICATION_SCOPE,
            redirect_uri=REDIRECT_URI
        )
    )

    # Grab some user data to create the playlist.
    user_id: str = spot.me()['id']
    playlist: dict = spot.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=public,
        description=CONVERTED_PLAYLIST_DESCRIPTION
    )
    playlist_id: str = playlist['id']
    playlist_url: str = playlist['external_urls']['spotify']

    # Search for each song's URI.
    song_uris: list = []
    for song, artist in tuples:
        query: str = f'track:{song} {artist}'
        search: dict = spot.search(query, limit=10, type='track')

        if search['tracks']['total'] > 0:
            top_result: dict = search['tracks']['items'][0]
            track_uri: str = top_result.get('uri')
            song_uris.append(track_uri)

        time.sleep(QUERY_SLEEP_TIME_SEC)

    # Add the songs to the playlist in chunks.
    request: int = 0
    while request * PLAYLIST_ITEM_ADD_LIMIT < len(song_uris):
        lower_bound: int = request * PLAYLIST_ITEM_ADD_LIMIT
        upper_bound: int = (request + 1) * PLAYLIST_ITEM_ADD_LIMIT
        spot.playlist_add_items(playlist_id, song_uris[lower_bound:upper_bound])
        request += 1

    return playlist_url


if __name__ == '__main__':
    print(convert_apple_music_playlist('https://music.apple.com/us/playlist/electronic-swing/pl.u-b3b8VPBHyWaR7GJ'))
