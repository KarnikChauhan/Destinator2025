import random  # pylint: disable=E0401
import re  # pylint: disable=E0401
from typing import Any, Dict, List, Optional  # pylint: disable=E0401

import disnake  # pylint: disable=C0302, C0114, E0401
import lavalink  # pylint: disable=E0401
from disnake.ext import commands  # pylint: disable=E0401
from lavalink import LoadType, Node  # pylint: disable=E0401
from lavalink.errors import ClientError  # pylint: disable=E0401
from lavalink.events import QueueEndEvent  # pylint: disable=E0401
from lavalink.events import TrackEndEvent  # pylint: disable=E0401
from lavalink.events import TrackExceptionEvent  # pylint: disable=E0401
from lavalink.events import TrackStartEvent  # pylint: disable=E0401; pylint: disable=E0401

from ext.logger import get_logger  # pylint: disable=E0401
from ext.utils import Utils  # pylint: disable=E0401

logger = get_logger("MusicCog")

# Regex pattern for URL validation
URL_RX = re.compile(r"https?://(?:www\.)?.+")
# Spotify URL patterns
SPOTIFY_URL_PATTERN = re.compile(
    r"https?://open.spotify.com/(?P<type>album|playlist|track|artist)/(?P<id>[a-zA-Z0-9]+)"
)


# noinspection PyMissingConstructor
class LavalinkVoiceClient(disnake.VoiceProtocol):
    """
    Implementation of Disnake's VoiceProtocol to work with Lavalink
    """

    def __init__(self, client: disnake.Client, channel: disnake.VoiceChannel):
        self.client = client
        self.channel = channel
        self.guild_id = channel.guild.id
        self._destroyed = False

        if not hasattr(self.client, "lavalink"):
            self.client.lavalink = lavalink.Client(client.user.id)
            # Configure your lavalink node details here
            self.client.lavalink.add_node(
                host="localhost",
                port=2333,
                password="youshallnotpass",
                region="us",
                name="default-node",
            )

        self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        """
        Called once the client recieves an update from discord's voice server
        :param data:
        :return:
        """
        lavalink_data = {"t": "VOICE_SERVER_UPDATE", "d": data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        """
        Called once the clinet recieves a voice state update
        :param data:
        :return:
        """
        channel_id = data["channel_id"]

        if not channel_id:
            await self._destroy()
            return

        self.channel = self.client.get_channel(int(channel_id))

        lavalink_data = {"t": "VOICE_STATE_UPDATE", "d": data}

        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(
        self,
        *,
        timeout: float,
        reconnect: bool,
        self_deaf: bool = True,
        self_mute: bool = False,
    ) -> None:
        """Connect to the voice channel"""
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(
            channel=self.channel, self_mute=self_mute, self_deaf=self_deaf
        )
        logger.info(
            f"Connected to voice channel {self.channel.name} in {self.channel.guild.name}"
        )

    async def disconnect(self, *, force: bool = False) -> None:
        """Disconnect from the voice channel"""
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        if not force and not player.is_connected:
            return

        await self.channel.guild.change_voice_state(channel=None)

        # Update the channel_id of the player to None
        player.channel_id = None
        await self._destroy()
        logger.info(f"Disconnected from voice channel in {self.channel.guild.name}")

    async def _destroy(self):
        """Clean up player resources"""
        self.cleanup()

        if self._destroyed:
            return

        self._destroyed = True

        try:
            await self.lavalink.player_manager.destroy(self.guild_id)
            logger.debug(f"Destroyed player for guild {self.guild_id}")
        except ClientError:
            pass


class MusicCog(commands.Cog):
    """
    Advanced Music Cog for Disnake with Lavalink
    Supports various music platforms and advanced controls
    """

    def __init__(self, bot):
        self.bot = bot
        self.utils = Utils()

        bot.loop.create_task(self._setup_lavalink())

        self._queue_history: Dict[
            int, List[Dict[str, Any]]
        ] = {}  # Store queue history per guild

        # Map of emojis for different music sources
        self.source_emojis = {
            "youtube": "🔴",
            "soundcloud": "🟠",
            "spotify": "🟢",
            "amazon": "🔵",  # For Prime Music
            "bandcamp": "🟣",
            "twitch": "🟣",
            "vimeo": "🔵",
            "http": "🌐",
            "local": "💻",
        }

        logger.info("Music cog initialized")

    async def _setup_lavalink(self):
        """Setup Lavalink once the bot is ready"""
        await self.bot.wait_until_ready()

        if not hasattr(self.bot, "lavalink"):
            self.bot.lavalink = lavalink.Client(self.bot.user.id)
            # Configure your lavalink node details here
            self.bot.lavalink.add_node(
                host="localhost",
                port=2333,
                password="youshallnotpass",
                region="us",
                name="default-node",
            )

        self.lavalink = self.bot.lavalink
        self.lavalink.add_event_hooks(self)
        logger.info("Lavalink setup complete")

    def cog_unload(self):
        """Clean up when the cog is unloaded"""
        if self.lavalink:
            # Close lavalink client
            self.lavalink.close()
            self.lavalink._event_hooks.clear()
        logger.info("Music cog unloaded")

    async def cog_slash_command_error(
        self, inter: disnake.ApplicationCommandInteraction, error: Exception
    ):
        """Handle errors from slash commands"""
        if isinstance(error, commands.CommandInvokeError):
            embed = disnake.Embed(
                title="❌ An error occurred",
                description=str(error.original),
                color=disnake.Color.red(),
            )
            try:
                await inter.response.send_message(embed=embed, ephemeral=True)
            except:  # pylint: disable=W0702
                await inter.edit_original_message(content="", embed=embed)

        else:
            embed = disnake.Embed(
                title="❌ An error occurred",
                description=str(error),
                color=disnake.Color.red(),
            )
            await inter.response.send_message(embed=embed, ephemeral=True)

        logger.error(f"Command error: {error}", exc_info=True)

    async def ensure_voice(
        self, inter: disnake.ApplicationCommandInteraction
    ) -> Optional[lavalink.DefaultPlayer]:
        """
        Ensure the bot is in a voice channel and the user meets the requirements
        """
        player = self.bot.lavalink.player_manager.get(inter.guild_id)

        # Handle guild check
        if not inter.guild:
            await inter.response.send_message(
                "This command cannot be used in DMs", ephemeral=True
            )
            return None

        # Handle voice state checks
        if not inter.author.voice or not inter.author.voice.channel:
            if player is not None and player.is_connected:
                await inter.response.send_message(
                    "You need to join my voice channel first", ephemeral=True
                )
            else:
                await inter.response.send_message(
                    "You need to join a voice channel first", ephemeral=True
                )
            return None

        voice_channel = inter.author.voice.channel

        # Create player if it doesn't exist
        if not player:
            player = self.bot.lavalink.player_manager.create(inter.guild_id)
            player.store("channel", inter.channel.id)
            logger.info(f"Created player for guild {inter.guild_id}")

        # Check if the user is in the same voice channel as the bot
        if player.is_connected:
            if player.channel_id != voice_channel.id:
                await inter.response.send_message(
                    "You need to be in my voice channel", ephemeral=True
                )
                return None
        else:
            # Check permissions before connecting
            permissions = voice_channel.permissions_for(inter.guild.me)
            if not permissions.connect or not permissions.speak:
                await inter.response.send_message(
                    "I need `CONNECT` and `SPEAK` permissions", ephemeral=True
                )
                return None

            # Check user limit
            if voice_channel.user_limit > 0:
                if (
                    len(voice_channel.members) >= voice_channel.user_limit
                    and not inter.guild.me.guild_permissions.move_members
                ):
                    await inter.response.send_message(
                        "Your voice channel is full!", ephemeral=True
                    )
                    return None

            # Connect to the channel
            player.store("channel", inter.channel.id)
            await voice_channel.connect(cls=LavalinkVoiceClient)
            logger.info(f"Connected to voice channel: {voice_channel.name}")

        return player

    def get_platform_emoji(self, track) -> str:
        """Get emoji for the music source"""
        track_source = track.source.lower() if hasattr(track, "source") else "http"
        return self.source_emojis.get(track_source, "🎵")

    async def fetch_spotify_tracks(self, spotify_url: str, node: Node) -> list:
        """
        Fetch tracks from Spotify URLs
        Uses Lavalink plugins like LavaSrc for Spotify support
        """

        match = SPOTIFY_URL_PATTERN.match(spotify_url)
        if not match:
            return []

        spotify_type = match.group("type")
        result = await node.get_tracks(spotify_url)

        if result.load_type == LoadType.PLAYLIST:
            logger.info(
                f"Loaded Spotify {spotify_type} with {len(result.tracks)} tracks"
            )
            return result.tracks
        elif result.load_type == LoadType.TRACK:
            logger.info("Loaded single Spotify track")
            return [result.tracks[0]]
        else:
            logger.warning(f"Failed to load Spotify URL: {spotify_url}")
            return []

    @lavalink.listener(TrackStartEvent)
    async def on_track_start(self, event: TrackStartEvent):
        """Event fired when a track starts playing"""
        guild_id = event.player.guild_id
        channel_id = event.player.channel_id
        guild = self.bot.get_guild(guild_id)

        if not guild:
            await self.lavalink.player_manager.destroy(guild_id)
            return

        channel = guild.get_channel(channel_id)
        track = event.track

        # Store track in history
        if guild_id not in self._queue_history:
            self._queue_history[guild_id] = []

        # Add to history, keep last 10 tracks
        track_info = {
            "title": track.title,
            "author": track.author,
            "uri": track.uri,
            "identifier": track.identifier,
            "source": track.source if hasattr(track, "source") else "unknown",
        }
        self._queue_history[guild_id].append(track_info)
        self._queue_history[guild_id] = self._queue_history[guild_id][-10:]

        if channel:
            emoji = self.get_platform_emoji(track)
            embed = disnake.Embed(
                title=f"{emoji} Now Playing",
                description=f"[{track.title}]({track.uri})",
                color=disnake.Color.blurple(),
            )

            embed.add_field(name="Artist", value=f"**{track.author}**")
            embed.add_field(name="Duration", value=self.format_time(track.duration))

            # Add requester info if available
            requester_id = event.player.current.extra.get("requester")
            if requester_id:
                requester = guild.get_member(requester_id)
                if requester:
                    embed.set_footer(
                        text=f"Requested by {requester.display_name}",
                        icon_url=requester.display_avatar.url,
                    )

            await channel.send(embed=embed)
            logger.info(f"Now playing in {guild.name}: {track.title} by {track.author}")

    @lavalink.listener(TrackEndEvent)
    async def on_track_end(self, event: TrackEndEvent):
        """Event fired when a track ends"""
        if event.reason == "REPLACED":
            return  # Ignore when tracks are replaced (skipped)

        guild_id = event.player.guild_id
        logger.debug(f"Track ended in guild {guild_id}: {event.track.title}")

    @lavalink.listener(QueueEndEvent)
    async def on_queue_end(self, event: QueueEndEvent):
        """Event fired when the queue ends"""
        guild_id = event.player.guild_id
        channel_id = event.player.channel_id
        guild = self.bot.get_guild(guild_id)

        if not guild:
            return

        channel = guild.get_channel(channel_id)

        # Disconnect after queue ends
        if guild.voice_client:
            await guild.voice_client.disconnect(force=True)

        if channel:
            await channel.send("Queue ended, disconnected from voice channel.")
            logger.info(f"Queue ended in {guild.name}")

    @lavalink.listener(TrackExceptionEvent)
    async def on_track_exception(self, event: TrackExceptionEvent):
        """Event fired when a track encounters an exception"""
        guild_id = event.player.guild_id
        channel_id = event.player.channel_id
        guild = self.bot.get_guild(guild_id)

        if not guild:
            return

        channel = guild.get_channel(channel_id)

        if channel:
            error_embed = disnake.Embed(
                title="❌ Error playing track",
                description=f"An error occurred while playing the track: {event.cause}",
                color=disnake.Color.red(),
            )
            await channel.send(embed=error_embed)

            logger.error(f"Track exception in {guild.name}: {event.cause}")

    def format_time(self, ms: int) -> str:
        """Format milliseconds to a time string"""
        seconds = ms // 1000
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

    @commands.slash_command(name="play")
    async def play(
        self,
        inter: disnake.ApplicationCommandInteraction,
        query: str = commands.Param(description="Song name or URL to play"),
    ):
        """Search and play a song"""
        await inter.response.defer()

        player = await self.ensure_voice(inter)
        if not player:
            return

        # Remove leading and trailing <>
        query = query.strip("<>")

        # Determine source and search strategy
        if URL_RX.match(query):
            # Handle URLs
            if "spotify.com" in query:
                node = player.node
                tracks = await self.fetch_spotify_tracks(query, node)
                if not tracks:
                    embed = disnake.Embed(
                        title="❌ Error",
                        description="No tracks found for that Spotify link",
                        color=disnake.Color.red(),
                    )
                    return await inter.followup.send(embed=embed)

                # Add tracks to queue
                for track in tracks:
                    player.add(track=track, requester=inter.author.id)

                if len(tracks) > 1:
                    emoji = self.get_platform_emoji(tracks[0])
                    embed = disnake.Embed(
                        title=f"{emoji} Spotify Playlist Enqueued",
                        description=f"Added {len(tracks)} tracks from Spotify to the queue",
                        color=disnake.Color.blurple(),
                    )
                    await inter.followup.send(embed=embed)
                else:
                    emoji = self.get_platform_emoji(tracks[0])
                    embed = disnake.Embed(
                        title=f"{emoji} Spotify Track Enqueued",
                        description=f"Added [{tracks[0].title}]({tracks[0].uri}) to the queue",
                        color=disnake.Color.blurple(),
                    )
                    await inter.followup.send(embed=embed)
            else:
                # Handle other URLs
                results = await player.node.get_tracks(query)

                if results.load_type == LoadType.EMPTY:
                    embed = disnake.Embed(
                        title="❌ Error",
                        description="Couldn't find any tracks for that query",
                        color=disnake.Color.red(),
                    )
                    return await inter.followup.send(embed=embed)
                elif results.load_type == LoadType.PLAYLIST:
                    tracks = results.tracks

                    # Add all tracks from playlist to queue
                    for track in tracks:
                        player.add(track=track, requester=inter.author.id)
                    emoji = self.get_platform_emoji(tracks[0])
                    embed = disnake.Embed(
                        title=f"{emoji} Playlist Enqueued",
                        description=f"{results.playlist_info.name} - {len(tracks)} tracks",
                        color=disnake.Color.blurple(),
                    )
                    await inter.followup.send(embed=embed)
                else:
                    track = results.tracks[0]
                    player.add(track=track, requester=inter.author.id)
                    emoji = self.get_platform_emoji(track)
                    embed = disnake.Embed(
                        title=f"{emoji} Track Enqueued",
                        description=f"[{track.title}]({track.uri})",
                        color=disnake.Color.blurple(),
                    )
                    embed.add_field(name="Artist", value=track.author)
                    embed.add_field(
                        name="Duration", value=self.format_time(track.duration)
                    )
                    await inter.followup.send(embed=embed)
        else:
            # Handle search queries
            # Yt first
            results = await player.node.get_tracks(f"ytsearch:{query}")

            if not results or results.load_type == LoadType.EMPTY or not results.tracks:
                results = await player.node.get_tracks(f"scsearch:{query}")

            if not results or results.load_type == LoadType.EMPTY or not results.tracks:
                embed = disnake.Embed(
                    title="❌ Error",
                    description="Couldn't find any tracks for that query",
                    color=disnake.Color.red(),
                )
                return await inter.followup.send(embed=embed)

            # Add the first result to the queue
            track = results.tracks[0]
            player.add(track=track, requester=inter.author.id)

            emoji = self.get_platform_emoji(track)
            embed = disnake.Embed(
                title=f"{emoji} Track Enqueued",
                description=f"[{track.title}]({track.uri})",
                color=disnake.Color.blurple(),
            )
            embed.add_field(name="Artist", value=track.author)
            embed.add_field(name="Duration", value=self.format_time(track.duration))
            await inter.followup.send(embed=embed)

        # Play if not already playing
        if not player.is_playing:
            await player.play()

    @commands.slash_command(name="search")
    async def search(
        self,
        inter: disnake.ApplicationCommandInteraction,
        query: str = commands.Param(description="What song to search for"),
        platform: str = commands.Param(
            description="Platform to search on",
            choices=["YouTube", "SoundCloud", "All"],
            default="All",
        ),
    ):
        """Search for songs and select one to play"""
        await inter.response.defer()

        player = await self.ensure_voice(inter)
        if not player:
            return

        # Search based on platform
        tracks = []
        if platform in ["YouTube", "All"]:
            results = await player.node.get_tracks(f"ytsearch:{query}")
            if results and results.tracks:
                tracks.extend(results.tracks[:5])  # Take top 5 YouTube results

        if platform in ["SoundCloud", "All"] and len(tracks) < 10:
            results = await player.node.get_tracks(f"scsearch:{query}")
            if results and results.tracks:
                tracks.extend(results.tracks[:5])  # Take top 5 SoundCloud results

        if not tracks:
            embed = disnake.Embed(
                title="❌ Error",
                description="Couldn't find any tracks for that query",
                color=disnake.Color.red(),
            )
            return await inter.followup.send(embed=embed)

        # Limit to 10 total results
        tracks = tracks[:10]

        # Create select menu options
        options = []
        for i, track in enumerate(tracks):
            emoji = self.get_platform_emoji(track)
            duration = self.format_time(track.duration)
            source = track.source if hasattr(track, "source") else "unknown"

            # Truncate long titles
            title = track.title
            if len(title) > 90:
                title = title[:87] + "..."

            options.append(
                disnake.SelectOption(
                    label=f"{i + 1}. {title[:97]}",
                    description=f"{track.author} • {duration} • {source.upper()}",
                    value=str(i),
                    emoji=emoji,
                )
            )

        # Create select menu component
        select = disnake.ui.Select(
            placeholder="Select a song to play",
            options=options,
            custom_id="search_results",
        )

        # Store tracks for retrieval when selection is made
        view = disnake.ui.View(timeout=60)
        view.add_item(select)

        # Store the tracks temporarily
        self.bot._search_results = {f"{inter.guild_id}_{inter.author.id}": tracks}

        # When a track is selected
        async def select_callback(select_inter: disnake.MessageInteraction):
            if select_inter.author.id != inter.author.id:
                embed = disnake.Embed(
                    title="❌ Error",
                    description="You cannot use this selection menu.",
                    color=disnake.Color.red(),
                )
                return await select_inter.response.send_message(
                    embed=embed, ephemeral=True
                )

            # Retrieve tracks from storage
            result_key = f"{inter.guild_id}_{inter.author.id}"
            stored_tracks = self.bot._search_results.get(result_key, [])

            if not stored_tracks:
                embed = disnake.Embed(
                    title="❌ Error",
                    description="Search results expired. Please search again.",
                    color=disnake.Color.red(),
                )
                return await select_inter.response.send_message(
                    embed=embed, ephemeral=True
                )

            index = int(select_inter.values[0])
            track = stored_tracks[index]

            # Add to queue
            player = self.bot.lavalink.player_manager.get(select_inter.guild_id)
            if not player:
                embed = disnake.Embed(
                    title="❌ Error",
                    description="Player no longer exists. Please try again.",
                    color=disnake.Color.red(),
                )
                return await select_inter.response.send_message(
                    embed=embed, ephemeral=True
                )

            player.add(track=track, requester=select_inter.author.id)

            # Create confirmation embed
            emoji = self.get_platform_emoji(track)
            embed = disnake.Embed(
                title=f"{emoji} Track Enqueued",
                description=f"[{track.title}]({track.uri})",
                color=disnake.Color.blurple(),
            )
            embed.add_field(name="Artist", value=track.author)
            embed.add_field(name="Duration", value=self.format_time(track.duration))
            embed.set_footer(
                text=f"Requested by {select_inter.author.display_name}",
                icon_url=select_inter.author.display_avatar.url,
            )

            # Play if not already playing
            if not player.is_playing:
                await player.play()

            # Clean up stored results
            if result_key in self.bot._search_results:
                del self.bot._search_results[result_key]

            await select_inter.response.edit_message(embed=embed, view=None)

        select.callback = select_callback

        # Create results embed
        embed = disnake.Embed(
            title=f"Search Results for '{query}'",
            description="Select a track to play",
            color=disnake.Color.blurple(),
        )

        await inter.followup.send(embed=embed, view=view)

    @commands.slash_command(name="queue")
    async def queue(
        self,
        inter: disnake.ApplicationCommandInteraction,
        page: int = commands.Param(description="Page number to view", default=1, ge=1),
    ):
        """View the current song queue"""
        player = self.bot.lavalink.player_manager.get(inter.guild_id)

        if not player or not player.queue:
            embed = disnake.Embed(
                title="❌ Error",
                description="No tracks found for that Spotify link",
                color=disnake.Color.red(),
            )
            return await inter.followup.send(embed=embed)

        # Calculate pages
        items_per_page = 10
        pages = max(1, (len(player.queue) + items_per_page - 1) // items_per_page)

        if page > pages:
            page = pages

        # Calculate start and end indices
        start = (page - 1) * items_per_page
        end = min(start + items_per_page, len(player.queue))

        # Create embed
        embed = disnake.Embed(title="Current Queue", color=disnake.Color.blurple())

        # Add current track
        if player.is_playing:
            current = player.current
            self.format_time(current.duration)
            self.format_time(player.position)
            emoji = self.get_platform_emoji(current)

            embed.add_field(
                name="Now Playing",
                value=f"{emoji} **[{current.title}]({current.uri})**"
                "`[{current_pos}/{current_duration}]`\n"
                f"Requested by: <@{current.extra.get('requester', 'Unknown')}>",
                inline=False,
            )

        # List queue
        if player.queue:
            queue_list = []
            for i, track in enumerate(player.queue[start:end], start=start + 1):
                emoji = self.get_platform_emoji(track)
                duration = self.format_time(track.duration)
                requester = track.extra.get("requester", "Unknown")

                queue_list.append(
                    f"`{i}.` {emoji} **[{track.title}]({track.uri})** `[{duration}]`\n"
                    f"┗ Requested by: <@{requester}>"
                )

            embed.description = "\n\n".join(queue_list)

        # Add pagination info
        embed.set_footer(
            text=f"Page {page}/{pages} • {len(player.queue)} songs in queue"
        )

        # Queue stats
        total_length = sum(t.duration for t in player.queue)
        embed.add_field(
            name="Queue Info",
            value=f"**{len(player.queue)}** tracks | "
            f"`{self.format_time(total_length)}` total length",
            inline=False,
        )

        # Create pagination controls
        view = disnake.ui.View(timeout=60)

        # Previous page button
        previous_button = disnake.ui.Button(
            emoji="⬅️", style=disnake.ButtonStyle.gray, disabled=(page == 1)
        )

        # Next page button
        next_button = disnake.ui.Button(
            emoji="➡️", style=disnake.ButtonStyle.gray, disabled=(page == pages)
        )

        async def previous_callback(button_inter: disnake.MessageInteraction):
            if button_inter.author.id != inter.author.id:
                embed = disnake.Embed(
                    title="❌ Error",
                    description="You cannot use theese controls.",
                    color=disnake.Color.red(),
                )
                return await button_inter.response.send_message(
                    embed=embed, ephemeral=True
                )

            nonlocal page
            page -= 1
            await self.update_queue_message(button_inter, page, items_per_page)

        async def next_callback(button_inter: disnake.MessageInteraction):
            if button_inter.author.id != inter.author.id:
                embed = disnake.Embed(
                    title="❌ Error",
                    description="You cannot use theese controls.",
                    color=disnake.Color.red(),
                )
                return await button_inter.response.send_message(
                    embed=embed, ephemeral=True
                )

            nonlocal page
            page += 1
            await self.update_queue_message(button_inter, page, items_per_page)

        previous_button.callback = previous_callback
        next_button.callback = next_callback

        view.add_item(previous_button)
        view.add_item(next_button)

        await inter.response.send_message(embed=embed, view=view)

    async def update_queue_message(
        self, inter: disnake.MessageInteraction, page: int, items_per_page: int
    ):
        """Update the queue message with new page"""
        player = self.bot.lavalink.player_manager.get(inter.guild_id)

        if not player or not player.queue:
            return await inter.response.edit_message(
                content="Queue is now empty", embed=None, view=None
            )

        # Calculate pages
        pages = max(1, (len(player.queue) + items_per_page - 1) // items_per_page)

        if page > pages:
            page = pages

        # Calculate start and end indices
        start = (page - 1) * items_per_page
        end = min(start + items_per_page, len(player.queue))

        # Create embed
        embed = disnake.Embed(title="Current Queue", color=disnake.Color.blurple())

        # Add current track
        if player.is_playing:
            current = player.current
            current_duration = self.format_time(current.duration)
            current_pos = self.format_time(player.position)
            emoji = self.get_platform_emoji(current)

            embed.add_field(
                name="Now Playing",
                value=f"{emoji} **[{current.title}]"
                f"({current.uri})** `[{current_pos}/{current_duration}]`\n"
                f"Requested by: <@{current.extra.get('requester', 'Unknown')}>",
                inline=False,
            )

        # List queue
        if player.queue:
            queue_list = []
            for i, track in enumerate(player.queue[start:end], start=start + 1):
                emoji = self.get_platform_emoji(track)
                duration = self.format_time(track.duration)
                requester = track.extra.get("requester", "Unknown")

                queue_list.append(
                    f"`{i}.` {emoji} **[{track.title}]({track.uri})** `[{duration}]`\n"
                    f"┗ Requested by: <@{requester}>"
                )

            embed.description = "\n\n".join(queue_list)

        # Add pagination info
        embed.set_footer(
            text=f"Page {page}/{pages} • {len(player.queue)} songs in queue"
        )

        # Queue stats
        total_length = sum(t.duration for t in player.queue)
        embed.add_field(
            name="Queue Info",
            value=f"**{len(player.queue)}** tracks | "
            f"`{self.format_time(total_length)}` total length",
            inline=False,
        )

        # Update pagination controls
        view = disnake.ui.View(timeout=60)

        # Previous page button
        previous_button = disnake.ui.Button(
            emoji="⬅️", style=disnake.ButtonStyle.gray, disabled=(page == 1)
        )

        # Next page button
        next_button = disnake.ui.Button(
            emoji="➡️", style=disnake.ButtonStyle.gray, disabled=(page == pages)
        )

        async def previous_callback(button_inter: disnake.MessageInteraction):
            if button_inter.author.id != inter.author.id:
                embed = disnake.Embed(
                    title="❌ Error",
                    description="You cannot use theese controls.",
                    color=disnake.Color.red(),
                )
                return await button_inter.response.send_message(
                    embed=embed, ephemeral=True
                )

            nonlocal page
            page -= 1
            await self.update_queue_message(button_inter, page, items_per_page)

        async def next_callback(button_inter: disnake.MessageInteraction):
            if button_inter.author.id != inter.author.id:
                embed = disnake.Embed(
                    title="❌ Error",
                    description="You cannot use theese controls.",
                    color=disnake.Color.red(),
                )
                return await button_inter.response.send_message(
                    embed=embed, ephemeral=True
                )

            nonlocal page
            page += 1
            await self.update_queue_message(button_inter, page, items_per_page)

        previous_button.callback = previous_callback
        next_button.callback = next_callback

        view.add_item(previous_button)
        view.add_item(next_button)

        await inter.response.edit_message(embed=embed, view=view)

    @commands.slash_command(name="skip")
    async def skip(
        self,
        inter: disnake.ApplicationCommandInteraction,
        index: int = commands.Param(
            description="Skip to specific position in queue", default=None, ge=1
        ),
    ):
        """Skip the current track or to a specific position"""
        player = self.bot.lavalink.player_manager.get(inter.guild_id)

        if not player or not player.is_playing:
            embed = disnake.Embed(
                title="❌ Error",
                description="Nothing is playing right now",
                color=disnake.Color.red(),
            )

            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Skip current or skip to position
        if index is None:
            # Skip current track
            current = player.current
            await player.skip()
            embed = disnake.Embed(
                title="⏭️ Skipped Track",
                description=f"Track Title: **{current.title}**",
                color=disnake.Color.red(),
            )
            await inter.response.send_message(embed=embed)
            logger.info(f"Skipped track in {inter.guild.name}: {current.title}")
        else:
            # Skip to position
            if index > len(player.queue):
                embed = disnake.Embed(
                    title="❌ Error",
                    description=f"There are only {len(player.queue)} songs in the queue",
                    color=disnake.Color.red(),
                )
                return await inter.response.send_message(embed=embed, ephemeral=True)

            # Calculate position (0-based)
            pos = index - 1

            # Store the track info for confirmation message
            skipped_to = player.queue[pos]

            # Remove tracks before the selected position
            for _ in range(pos):
                player.queue.pop(0)

            # Skip current track to start next one
            await player.skip()
            embed = disnake.Embed(
                title="⏭️ Skipped to position",
                description=f"Skipped to position **{index}**: **{skipped_to.title}**",
                color=disnake.Color.red(),
            )
            await inter.response.send_message(embed=embed)
            logger.info(f"Skipped to position {index} in {inter.guild.name}")

    @commands.slash_command(name="stop")
    async def stop(self, inter: disnake.ApplicationCommandInteraction):
        """Stop playing and clear the queue"""
        player = await self.ensure_voice(inter)
        if not player:
            return

        # Clear queue and stop playback
        player.queue.clear()
        await player.stop()

        # Disconnect from voice
        guild = inter.guild
        if guild.voice_client:
            await guild.voice_client.disconnect(force=True)
        embed = disnake.Embed(
            title="⏹️ Stopped playback",
            description="Stopped playback and cleared the queue",
            color=disnake.Color.red(),
        )
        await inter.response.send_message(embed=embed)
        logger.info(f"Stopped playback in {inter.guild.name}")

    @commands.slash_command(name="pause")
    async def pause(self, inter: disnake.ApplicationCommandInteraction):
        """Pause the current track"""
        player = self.bot.lavalink.player_manager.get(inter.guild_id)

        if not player or not player.is_playing:
            embed = disnake.Embed(
                title="❌ Error",
                description="Nothing is playing right now",
                color=disnake.Color.red(),
            )
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Check if already paused
        if player.paused:
            embed = disnake.Embed(
                title="❌ Error",
                description="Playback is already paused",
                color=disnake.Color.red(),
            )
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Pause playback
        await player.set_pause(True)
        embed = disnake.Embed(
            title="⏹️ Paused playback",
            description="Paused playback",
            color=disnake.Color.red(),
        )
        await inter.response.send_message(embed=embed)
        logger.info(f"Paused playback in {inter.guild.name}")

    @commands.slash_command(name="resume")
    async def resume(self, inter: disnake.ApplicationCommandInteraction):
        """Resume playback"""
        player = self.bot.lavalink.player_manager.get(inter.guild_id)

        if not player or not player.is_playing:
            embed = disnake.Embed(
                title="❌ Error",
                description="Nothing is playing right now",
                color=disnake.Color.red(),
            )
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Check if already playing
        if not player.paused:
            embed = disnake.Embed(
                title="❌ Error",
                description="Playback is already paused",
                color=disnake.Color.red(),
            )
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Resume playback
        await player.set_pause(False)
        embed = disnake.Embed(
            title="⏹️ Resumed playback",
            description="Resumed playback",
            color=disnake.Color.red(),
        )
        await inter.response.send_message(embed=embed)
        logger.info(f"Resumed playback in {inter.guild.name}")

    @commands.slash_command(name="volume")
    async def volume(
        self,
        inter: disnake.ApplicationCommandInteraction,
        level: int = commands.Param(description="Volume level (0-100)", ge=0, le=100),
    ):
        """Set the playback volume"""
        player = await self.ensure_voice(inter)
        if not player:
            return

        # Set volume
        await player.set_volume(level)

        # Create volume bar visualization
        volume_bars = min(10, round(level / 10))
        bar = "🔊 " + "█" * volume_bars + "░" * (10 - volume_bars)

        await inter.response.send_message(f"Volume set to **{level}%**\n{bar}")
        logger.info(f"Volume set to {level}% in {inter.guild.name}")

    @commands.slash_command(name="nowplaying")
    async def nowplaying(self, inter: disnake.ApplicationCommandInteraction):
        """Show information about the current song"""
        player = self.bot.lavalink.player_manager.get(inter.guild_id)

        if not player or not player.is_playing:
            embed = disnake.Embed(
                title="❌ Error",
                description="Nothing is playing right now",
                color=disnake.Color.red(),
            )
            return await inter.response.send_message(embed=embed, ephemeral=True)

        track = player.current
        position = player.position

        # Calculate progress bar
        duration = track.duration
        if duration == 0:  # For streams
            prog_bar = "🔴 LIVE"
        else:
            # Create progress bar with 15 segments
            segments = 15
            progress = int(position / duration * segments)
            prog_bar = "▬" * progress + "🔘" + "▬" * (segments - progress)

        # Format times
        current_time = self.format_time(position)
        total_time = "∞" if duration == 0 else self.format_time(duration)

        # Create embed
        emoji = self.get_platform_emoji(track)
        embed = disnake.Embed(
            title=f"{emoji} Now Playing",
            description=f"[{track.title}]({track.uri})",
            color=disnake.Color.blurple(),
        )

        embed.add_field(name="Artist", value=track.author, inline=True)
        embed.add_field(
            name="Duration", value=f"{current_time} / {total_time}", inline=True
        )

        # Add progress bar
        embed.add_field(name="Progress", value=prog_bar, inline=False)

        # Add requester info
        requester_id = track.extra.get("requester")
        if requester_id:
            requester = inter.guild.get_member(requester_id)
            if requester:
                embed.set_footer(
                    text=f"Requested by {requester.display_name}",
                    icon_url=requester.display_avatar.url,
                )

        # Player stats
        player_stats = []
        if player.paused:
            player_stats.append("⏸️ Paused")
        if player.volume != 100:
            player_stats.append(f"🔊 Volume: {player.volume}%")
        if player.shuffle:
            player_stats.append("🔀 Shuffle: On")
        if player.loop:
            player_stats.append("🔁 Repeat: On")

        if player_stats:
            embed.add_field(
                name="Player Status", value=" | ".join(player_stats), inline=False
            )

        await inter.response.send_message(embed=embed)

    """
    @commands.slash_command(name="shuffle")
    async def shuffle(self, inter: disnake.ApplicationCommandInteraction):

        player = await self.ensure_voice(inter)
        if not player:
            return


        #player.shuffle = not player.shuffle
        player.custom_shuffle = player.shuffle # not tested
        if player.custom_shuffle:
            random.shuffle(player.queue)
            await inter.response.send_message("🔀 Shuffle mode **enabled**")
        else:
            await inter.response.send_message("🔀 Shuffle mode **disabled**")

        logger.info(f"Shuffle set to {player.shuffle} in {inter.guild.name}")
    """

    @commands.slash_command(name="shuffle")
    async def shuffle(self, inter: disnake.ApplicationCommandInteraction):
        """Shuffle the current queue"""
        player = self.bot.lavalink.player_manager.get(inter.guild_id)
        if not player:
            return

        random.shuffle(player.queue)
        emoji = "🔀"
        embed = disnake.Embed(
            title=f"{emoji} Queue Shuffled ",
            description="Queue has been shuffled randomically",
            color=disnake.Color.blurple(),
        )
        await inter.response.send_message(embed=embed)
        logger.info(f"Queue shuffled in {inter.guild.name}")

    @commands.slash_command(name="playnext")
    async def playnext(
        self,
        inter: disnake.ApplicationCommandInteraction,
        index: int = commands.Param(description="Position in queue to play next", ge=1),
    ):
        """Play a specific song from the queue next"""
        player = self.bot.lavalink.player_manager.get(inter.guild_id)

        if not player or not player.queue:
            embed = disnake.Embed(
                title="❌ Error",
                description="The queue is empty",
                color=disnake.Color.red(),
            )
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Check if valid index
        if index > len(player.queue):
            embed = disnake.Embed(
                title="❌ Error",
                description=f"There are only {len(player.queue)} songs in the queue",
                color=disnake.Color.red(),
            )
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Adjust for 0-based indexing
        index = index - 1

        # Get the track to play next
        track = player.queue.pop(index)

        # Insert the track at the top of the queue
        player.queue.insert(0, track)

        # Skip the current track to play the selected one
        await player.skip()
        embed = disnake.Embed(
            title="⏭️ Song skipped",
            description=f"Playing **{track.title}** next",
            color=disnake.Color.blurple(),
        )
        await inter.response.send_message(embed=embed, ephemeral=False)

        logger.info(f"Playing next track in {inter.guild.name}: {track.title}")

    @commands.slash_command(name="repeat")
    async def repeat(
        self,
        inter: disnake.ApplicationCommandInteraction,
        mode: str = commands.Param(
            description="Repeat mode", choices=["off", "one", "all"], default="all"
        ),
    ):
        """Set repeat mode (off, track, or queue)"""
        player = await self.ensure_voice(inter)
        if not player:
            return
        embed = disnake.Embed(
            title="🔁 Repeaat mode",
            description=f"Repeat mode changed to {mode}",
            color=disnake.Color.blurple(),
        )
        # Set repeat mode
        if mode == "off":
            player.repeat = False

            player.set_loop(0)  # Lavalink repeat mode off
            await inter.response.send_message(embed=embed)
        elif mode == "one":
            player.repeat = True
            player.set_loop(1)  # Lavalink repeat single track
            await inter.response.send_message(embed=embed)
        else:  # mode == "all"
            player.repeat = True
            player.set_loop(2)  # Lavalink repeat queue
            await inter.response.send_message(embed=embed)

        logger.info(f"Repeat mode set to {mode} in {inter.guild.name}")

    @commands.slash_command(name="remove")
    async def remove(
        self,
        inter: disnake.ApplicationCommandInteraction,
        index: int = commands.Param(description="Position in queue to remove", ge=1),
    ):
        """Remove a track from the queue"""
        player = self.bot.lavalink.player_manager.get(inter.guild_id)

        if not player or not player.queue:
            embed = disnake.Embed(
                title="❌ Error",
                description="The queue is empty",
                color=disnake.Color.red(),
            )
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Check if valid index
        if index > len(player.queue):
            embed = disnake.Embed(
                title="❌ Error",
                description=f"There are only {len(player.queue)} songs in the queue",
                color=disnake.Color.red(),
            )
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Adjust for 0-based indexing
        index = index - 1

        # Store removed track for confirmation
        removed = player.queue[index]

        # Remove track
        del player.queue[index]
        embed = disnake.Embed(
            title="❌ Song removed",
            description=f"Removed **{removed.title}** from the queue",
            color=disnake.Color.blurple(),
        )
        await inter.response.send_message(embed=embed, ephemeral=False)

        logger.info(f"Removed track from queue in {inter.guild.name}: {removed.title}")

    @commands.slash_command(name="clear")
    async def clear(self, inter: disnake.ApplicationCommandInteraction):
        """Clear the queue but keep current song"""
        player = self.bot.lavalink.player_manager.get(inter.guild_id)

        if not player or not player.queue:
            embed = disnake.Embed(
                title="❌ Error",
                description="The queue is already empty",
                color=disnake.Color.red(),
            )
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Store queue length for confirmation
        queue_length = len(player.queue)

        # Clear queue
        player.queue.clear()
        embed = disnake.Embed(
            title="🧹 Queue Cleared",
            description=f"Cleared {queue_length} songs from the queue",
            color=disnake.Color.blurple(),
        )
        await inter.response.send_message(embed=embed)
        logger.info(f"Cleared queue in {inter.guild.name}")

    @commands.slash_command(name="seek")
    async def seek(
        self,
        inter: disnake.ApplicationCommandInteraction,
        position: str = commands.Param(description="Position to seek to (e.g. '1:30')"),
    ):
        """Seek to a specific position in the current track"""
        player = self.bot.lavalink.player_manager.get(inter.guild_id)

        if not player or not player.is_playing:
            embed = disnake.Embed(
                title="❌ Error",
                description="Nothing is playing right now",
                color=disnake.Color.red(),
            )
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Parse time input
        seconds = 0
        try:
            # Handle mm:ss format
            if ":" in position:
                parts = position.split(":")
                if len(parts) == 2:  # mm:ss
                    seconds = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:  # hh:mm:ss
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            else:
                # Handle raw seconds
                seconds = int(position)
        except ValueError:
            embed = disnake.Embed(
                title="❌ Error",
                description="Invalid time format. Use 'mm:ss', 'hh:mm:ss', or seconds.",
                color=disnake.Color.red(),
            )

            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Convert to milliseconds
        ms = seconds * 1000

        # Check if position is valid
        if player.current.duration > 0 and ms > player.current.duration:
            embed = disnake.Embed(
                title="❌ Error",
                description="Cannot seek past the end of the track",
                color=disnake.Color.red(),
            )

            return await inter.response.send_message(embed=embed, ephemeral=True)

        if player.current.duration > 0 and ms > player.current.duration:
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Perform seek
        await player.seek(ms)
        embed = disnake.Embed(
            title="⏩ Song seeked",
            description=f"Seeked to **{self.format_time(ms)}**",
            color=disnake.Color.blurple(),
        )
        await inter.response.send_message(embed=embed)
        logger.info(f"Seeked to {self.format_time(ms)} in {inter.guild.name}")

    @commands.slash_command(name="disconnect")
    async def disconnect(self, inter: disnake.ApplicationCommandInteraction):
        """Disconnect from voice channel"""
        player = self.bot.lavalink.player_manager.get(inter.guild_id)

        if not player or not player.is_connected:
            embed = disnake.Embed(
                title="❌ Error",
                description="Im not connected to a voice channel",
                color=disnake.Color.red(),
            )
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Clear queue and stop playback
        player.queue.clear()
        await player.stop()

        # Disconnect
        guild = inter.guild
        if guild.voice_client:
            await guild.voice_client.disconnect(force=True)

        embed = disnake.Embed(
            title="👋 Bye Bye!",
            description="Disconnected from voice channel",
            color=disnake.Color.blurple(),
        )

        await inter.response.send_message(embed=embed)
        logger.info(f"Disconnected from voice in {inter.guild.name}")

    @commands.slash_command(name="history")
    async def history(self, inter: disnake.ApplicationCommandInteraction):
        """Show recently played tracks"""
        guild_id = inter.guild_id

        if guild_id not in self._queue_history or not self._queue_history[guild_id]:
            embed = disnake.Embed(
                title="❌ Error",
                description="No queue history available",
                color=disnake.Color.red(),
            )
            return await inter.response.send_message(embed=embed, ephemeral=True)

        # Create embed with history
        embed = disnake.Embed(
            title="Recently Played Tracks", color=disnake.Color.blurple()
        )

        # List tracks in reverse order (most recent first)
        history_list = []
        for i, track in enumerate(reversed(self._queue_history[guild_id]), start=1):
            title = track.get("title", "Unknown")
            author = track.get("author", "Unknown")
            uri = track.get("uri", "")
            source = track.get("source", "unknown")

            emoji = self.source_emojis.get(source.lower(), "🎵")

            if uri:
                history_list.append(f"`{i}.` {emoji} **[{title}]({uri})** by {author}")
            else:
                history_list.append(f"`{i}.` {emoji} **{title}** by {author}")

        embed.description = "\n".join(history_list)
        embed.set_footer(text=f"Total: {len(history_list)} tracks")

        await inter.response.send_message(embed=embed)


def setup(bot):
    """Setup function to add cog to bot"""
    bot.add_cog(MusicCog(bot))
    logger.info("Music cog loaded")
