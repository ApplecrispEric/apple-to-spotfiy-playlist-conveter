from flask import Flask, render_template, request, redirect, url_for
from conversion import convert_apple_music_playlist

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def submission():
    apple_playlist_url: str = request.form.get('apple_playlist_url')
    public_enabled: str = request.form.get('spotify_playlist_private_enabled')

    if 'https://music.apple.com/' not in apple_playlist_url:  # Invalid link.
        return redirect(url_for('index'))

    public: bool = public_enabled is not None

    try:
        playlist_url: str = convert_apple_music_playlist(apple_playlist_url=apple_playlist_url, public=public)
        return render_template('playlist.html', playlist_url=playlist_url)
    except Exception as exception:
        app.logger.info(exception)
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
