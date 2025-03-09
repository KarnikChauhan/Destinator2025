# Musipy - Advanced Discord Music Bot

Musipy is a powerful and versatile Discord music bot built with Disnake and Lavalink. It supports a wide range of music platforms, including YouTube, SoundCloud, Spotify, and more, offering advanced music playback and queue management features.

## Features

*   **Extensive Platform Support:** Plays music from YouTube, SoundCloud, Spotify, Amazon Music, Bandcamp, Twitch, and Vimeo.
*   **Slash Command Interface:** Easy-to-use slash commands for all music operations.
*   **Advanced Queue Management:** View, shuffle, repeat, remove, and clear the song queue.
*   **Search Functionality:** Search for tracks on YouTube and SoundCloud with interactive selection menus.
*   **Spotify Playlist Support:** Seamlessly play Spotify playlists and tracks.

*   **Now Playing Information:** Displays detailed information about the current track with a progress bar.
*   **History:** View recently played tracks.
*   **Customizable:** Configure Lavalink nodes and plugin settings via `application.yml`.

## Prerequisites

*   [Python 3.8+](https://www.python.org/downloads/)
*   [Lavalink.jar](https://github.com/freyacodes/Lavalink) (version 4.0 or higher)
*   [Java 11+](https://www.oracle.com/java/technologies/javase-jdk11-downloads.html) (for running Lavalink)
*   [Disnake](https://github.com/DisnakeDev/disnake)
*   A Discord bot token
*   A Spotify application client ID and secret (for Spotify support)
*   A Google account email and password

## Setup

1.  **Clone the repository:**

    ```sh
    git clone https://github.com/borgox/Musipy.git
    cd Musipy
    ```

2.  **Configure `application.yml`:**

    *   Rename `application.example.yml` to `application.yml`.
    *   Fill in your Lavalink server password, YouTube email/password (optional, but recommended for age-restricted content), and Spotify client ID/secret.

    ```yml
    lavalink:
      server:
        password: "your_lavalink_password"
      youtubeConfig:
        email: "your_youtube_email@gmail.com"
        password: "your_youtube_password"
      lavasrc:
        spotify:
          clientId: "your_spotify_client_id"
          clientSecret: "your_spotify_client_secret"
    ```
You can skip steps 3 to 5 and run with `./start.ps1` or `./start.sh`

3.  **Install dependencies:** 

    *   Create a virtual environment:

        ```sh
        python -m venv .venv
        ```

    *   Activate the virtual environment:

        *   **Linux/macOS:** `source .venv/bin/activate`
        *   **Windows:** `.\.venv\Scripts\activate`

    *   Install the required packages:

        ```sh
        python -m pip install -U pip
        python -m pip install -r requirements.txt
        ```

4.  **Start Lavalink:**

    *   Download the latest `lavalink.jar` from the [Lavalink releases page](https://github.com/freyacodes/Lavalink/releases).
    *   Place the `lavalink.jar` file in your Musipy project directory.
    *   Run Lavalink:

        ```sh
        java -jar lavalink.jar
        ```

5.  **Start the bot:**

    *   Obtain your Discord bot token from the [Discord Developer Portal](https://discord.com/developers/applications).
    *   Run the bot with the token:

        ```sh
        python src/main.py --token YOUR_DISCORD_BOT_TOKEN
        ```

        Alternatively, you can set the bot token in the `config/config.json` file.

## Configuration

The `application.yml` file is used to configure Lavalink and various plugin settings. Key configuration options include:

*   **Lavalink Server:**  `lavalink.server.password`
*   **YouTube Configuration:** `lavalink.youtubeConfig.email` and `lavalink.youtubeConfig.password` (for bypassing age restrictions)
*   **Spotify Configuration:** `lavalink.lavasrc.spotify.clientId` and `lavalink.lavasrc.spotify.clientSecret`

## Commands

*   `/play <query>`: Plays a song or adds it to the queue.  Supports URLs and search queries.
*   `/search <query> <platform>`: Searches for a song on YouTube or SoundCloud and presents a selection menu.
*   `/queue [page]`:  Displays the current song queue.
*   `/skip [index]`: Skips the current song or skips to a specific position in the queue.
*   `/stop`: Stops playback and clears the queue.
*   `/pause`: Pauses the current song.
*   `/resume`: Resumes the paused song.
*   `/volume <level>`: Sets the playback volume (0-100).
*   `/nowplaying`:  Shows information about the currently playing song.
*   `/shuffle`: Shuffles the current queue.
*   `/playnext <index>`: Plays a specific song from the queue next.
*   `/repeat <mode>`: Sets the repeat mode (off, one, all).
*   `/remove <index>`: Removes a track from the queue.
*   `/clear`: Clears the queue.
*   `/seek <position>`: Seeks to a specific position in the current track (e.g., 1:30).
*   `/disconnect`: Disconnects the bot from the voice channel.
*   `/history`: Shows recently played tracks.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bug fixes, new features, or improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.