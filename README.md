# 🎵 Musipy - Advanced Discord Music Bot

[![GitHub Stars](https://img.shields.io/github/stars/borgox/Musipy?style=for-the-badge)](https://github.com/borgox/Musipy/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/borgox/Musipy?style=for-the-badge)](https://github.com/borgox/Musipy/issues)
[![License](https://img.shields.io/github/license/borgox/Musipy?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue?style=for-the-badge)](https://www.python.org/downloads/)

Musipy is a powerful and versatile Discord music bot built with [Disnake](https://github.com/DisnakeDev/disnake) and [Lavalink](https://github.com/freyacodes/Lavalink). It provides seamless integration with multiple music platforms, including YouTube, SoundCloud, Spotify, and more, along with advanced music playback and queue management features.

---

## ✨ Features

- **Extensive Platform Support:**  
  Plays music from YouTube, SoundCloud, Spotify, Amazon Music, Bandcamp, Twitch, and Vimeo.
- **Slash Command Interface:**  
  Easy-to-use slash commands for all music operations.
- **Advanced Queue Management:**  
  View, shuffle, repeat, remove, and clear the song queue.
- **Search Functionality:**  
  Search for tracks on YouTube and SoundCloud with interactive selection menus.
- **Spotify Playlist Support:**  
  Seamlessly play Spotify playlists and tracks.
- **Now Playing Information:**  
  Displays detailed information about the current track, complete with a progress bar.
- **History:**  
  Keep track of recently played tracks.
- **Customizable:**  
  Configure Lavalink nodes and plugin settings via `application.yml`.

---

## 📌 Prerequisites

Before you start, ensure you have the following installed:

- [Python 3.8+](https://www.python.org/downloads/)
- [Lavalink.jar](https://github.com/freyacodes/Lavalink) (version 4.0 or higher)
- [Java 11+](https://www.oracle.com/java/technologies/javase-jdk11-downloads.html) (required to run Lavalink)
- [Disnake](https://github.com/DisnakeDev/disnake)
- A Discord bot token
- Spotify application client ID and secret (for Spotify support)
- A Google account email and password (for YouTube configuration)

---

## 🚀 Setup 

### 1️⃣ Clone the Repository

```sh
git clone https://github.com/borgox/Musipy.git
cd Musipy
```

### 2️⃣ Configure `application.yml`

- Rename `application.example.yml` to `application.yml`
- Fill in your Lavalink server password, YouTube email/password (optional, but recommended for age-restricted content), and Spotify client ID/secret.

> 💡 **Quick Start:** You can skip steps 3-5 by running `./start.ps1` (Windows) or `./start.sh` (Linux/macOS).

### 3️⃣ Install Dependencies

```sh
python -m venv .venv
# source .venv/bin/activate  # Linux/macOS
\.venv\Scripts\activate    # Windows
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### 4️⃣ Start Lavalink

1. Download the latest `lavalink.jar` from the [Lavalink releases page](https://github.com/freyacodes/Lavalink/releases). **(case sensitive name)**
2. Place `lavalink.jar` in the project root directory.
3. Run the following command to start Lavalink:
   ```sh
   java -jar lavalink.jar
   ```

### 5️⃣ Run the Bot

First obtain your Discord bot token by creating a new bot application on the [Discord Developer Portal](https://discord.com/developers/applications). Then run the bot with the following command:

```sh
python src/main.py --token YOUR_DISCORD_BOT_TOKEN
```

Alternatively, set the bot token in `config/config.json`.

---

## ⚙️ Configuration

The `application.yml` file handles Lavalink and various plugin settings. Key options include::

- **Lavalink Server:** `lavalink.server.password`
- **YouTube Config:** `lavalink.youtubeConfig.email` & `lavalink.youtubeConfig.password` (for bypassing age restrictions and bot detection)
- **Spotify API Keys:** `lavalink.lavasrc.spotify.clientId` & `lavalink.lavasrc.spotify.clientSecret`

---

## 🎛️ Commands 

Here are some of the primary slash commands supported by Musipy:

| Command              | Description                              |
| -------------------- | ---------------------------------------- |
| `/play <query>`      | Play a song or add it to the queue       |
| `/search <query>`    | Search for a track on YouTube/SoundCloud |
| `/queue`             | Show the current song queue              |
| `/skip [index]`      | Skip the current song or jump ahead      |
| `/stop`              | Stop playback and clear the queue        |
| `/pause` / `/resume` | Pause or resume playback                 |
| `/volume <level>`    | Adjust the volume (0-100)                |
| `/nowplaying`        | Show info about the current track        |
| `/shuffle`           | Shuffle the queue                        |
| `/playnext <index>`  | Play a specific song next                |
| `/repeat <mode>`     | Set repeat mode (off, one, all)          |
| `/remove <index>`    | Remove a song from the queue             |
| `/clear`             | Clear the queue                          |
| `/seek <position>`   | Seek to a position in the track          |
| `/disconnect`        | Disconnect the bot                       |
| `/history`           | View recently played songs               |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bug fixes, new features, or improvements.

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🌐 Connect with Me

Visit my website: [borgodev.me](https://borgodev.me) 🌍