from __future__ import print_function
import asyncio
import functools
import itertools
import math
import random
import ctypes
import ctypes.util
import sys
import spotipy
import spotipy.util as util
import discord
import youtube_dl
from async_timeout import timeout
from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials
import os

os.environ["SPOTIPY_CLIENT_ID"] ='21bb33d11bfb49bbbfa243c2c124cacb'
os.environ["SPOTIPY_CLIENT_SECRET"] ='3cbcadf170b04d69b0169b345f8c6d0f'
 
print("ctypes - Find opus:")
a = ctypes.util.find_library('opus')
print(a)
 
print("Discord - Load Opus:")
b = discord.opus.load_opus(a)
print(b)
 
print("Discord - Is loaded:")
c = discord.opus.is_loaded()
print(c)


youtube_dl.utils.bug_reports_message = lambda: ''

token='NzY4NzcxOTIwOTMzMDI3ODQx.X5FUpQ.3RgV5kAgF3nT8GRtFBzQ64NeH_w'
class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('OH NO `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('OH NO `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('OH NO `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title='Now playing',
                               description='```css\n{0.source.title}\n```'.format(self),
                               color=discord.Color.blurple())
                 .add_field(name='Duration', value=self.source.duration)
                 .add_field(name='Requested by', value=self.requester.mention)
                 .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                 .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                 .set_image(url=self.source.thumbnail))

        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:

                try:
                    async with timeout(9999999999999999):
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    return

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(embed=self.current.create_embed())

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('SORRY M8 NO DMS')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))

    @commands.command(name='join', invoke_without_subcommand=True)
    async def join(self, ctx: commands.Context):


        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='summon')
    @commands.has_permissions(manage_guild=True)
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):


        if not channel and not ctx.author.voice:
            raise VoiceError('You are neither connected to a voice channel nor specified a channel to join.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='leave', aliases=['disconnect','s'])
    @commands.has_permissions(manage_guild=True)
    async def leave(self, ctx: commands.Context):


        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel.')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name='volume')
    async def volume(self, ctx: commands.Context, *, volume: int):


        if not ctx.voice_state.is_playing:
            return await ctx.send('PLAY SOMETHING FIRST')

        if 0 > volume > 100:
            return await ctx.send('Volume must be between 0 and 100')

        ctx.voice_state.volume = volume / 100
        await ctx.send('Volume of the player set to {}%'.format(volume))

    @commands.command(name='now', aliases=['current', 'playing','np'])
    async def np(self, ctx: commands.Context):
      
        await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command(name='pause')
    @commands.has_permissions(manage_guild=True)
    async def pause(self, ctx: commands.Context):


        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='resume')
    @commands.has_permissions(manage_guild=True)
    async def resume(self, ctx: commands.Context):


        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')
         
    @commands.command(name='r')
    @commands.has_permissions(manage_guild=True)
    async def r(self, ctx: commands.Context):


        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='stop')
    @commands.has_permissions(manage_guild=True)
    async def stop(self, ctx: commands.Context):


        ctx.voice_state.songs.clear()

        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

    @commands.command(name='skip')
    async def skip(self, ctx: commands.Context):


        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.send('skip vote **{}/3**'.format(total_votes))

        else:
            await ctx.send("You've already voted")
    
    
    
    @commands.command(name='next')
    async def next(self, ctx: commands.Context):


        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music')

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.send('skip vote **{}/3**'.format(total_votes))

        else:
            await ctx.send("You've already voted!")
    
    
    
    @commands.command(name='skip')
    async def skip(self, ctx: commands.Context):


        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.send('Skip vote **{}/3**'.format(total_votes))

        else:
            await ctx.send("you've already voted!")
    
    @commands.command(name='fs')
    @commands.has_role('DJ' or 'dj')
    async def force(self, ctx: commands.Context):


        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')

        else:
            ctx.voice_state.skip()
    
    @commands.command(name='queue', aliases=['q'])
    async def q(self, ctx: commands.Context, *, page: int = 1):


        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='Viewing page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def shuffle(self, ctx: commands.Context):


        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove')
    async def remove(self, ctx: commands.Context, index: int):


        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='loop')
    async def loop(self, ctx: commands.Context):


        if not ctx.voice_state.is_playing:
            return await ctx.send('nothing is playing')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction('✅')

    @commands.command(name='play')
    async def play(self, ctx: commands.Context, *, search: str):


        if not ctx.voice_state.voice:
            await ctx.invoke(self.join)

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send('ERROR: {}'.format(str(e)))
            else:
                song = Song(source)

                await ctx.voice_state.songs.put(song)
                await ctx.send('Enqueued {}'.format(str(source)))
                await ctx.message.add_reaction('🎶')

                
    @commands.command(name='p')
    async def p(self, ctx: commands.Context, *, search: str):


        if not ctx.voice_state.voice:
            await ctx.invoke(self.join)

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send('FUCK THERE IS AN ERROR: {}'.format(str(e)))
            else:
                song = Song(source)

                await ctx.voice_state.songs.put(song)
                await ctx.send('Enqueued {}'.format(str(source)))
                await ctx.message.add_reaction('🎶')
                
    @commands.command(name='servers',pass_context=True)
    async def botservers(ctx):
            
         await client.say("I'm in " + str(len(client.servers)) + " servers")

    
  
    @commands.command(name='spotify')
    async def cmd_spotify(self, ctx: commands.Context, *,URL):
        if not ctx.voice_state.voice:
            await ctx.invoke(self.join)


        
        client_credentials_manager = SpotifyClientCredentials()
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        if ".spotify" and "track" in str(URL):
            track = str(URL)
            res = sp.track(track)
            song = res['name']
            artist = res['artists'][0]['name']
            songToPlay= str(song) + str(artist)
            try:
                    source= await YTDLSource.create_source(ctx,songToPlay, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send('OH NO ERROR: {}'.format(str(e)))

            else:
                song = Song(source)

                await ctx.voice_state.songs.put(song)
                await ctx.send('Enqueued {}'.format(str(source)))
                await ctx.message.add_reaction('🎶')


        elif ".spotify" and "album" in str(URL):
            album =str(URL)
            res = sp.album_tracks(album)
            for items in res["items"]:
                song = items["name"]
                artist = items["artists"][0]["name"]
                songToPlay = str(song) + str(artist)
                try:
                    source = await YTDLSource.create_source(ctx, songToPlay, loop=self.bot.loop)
                except YTDLError as e:
                    await ctx.send('OH NO ERROR:{}'.format(str(e)))
                else:
                    song = Song(source)

                    await ctx.voice_state.songs.put(song)
                    await ctx.send('Enqueued {}'.format(str(source)))
                    await ctx.message.add_reaction('🎶')


        elif ".spotify" and "playlist" in str(URL):
            playlist = str(URL)
            res = sp.playlist_tracks(playlist)
            for items in res["items"]:
                song = items["track"]["name"]
                artist = items["track"]["artists"][0]["name"]
                songToPlay = str(song) + str(artist)
                try:
                    source = await YTDLSource.create_source(ctx, songToPlay, loop=self.bot.loop)
                except YTDLError as e:
                    await ctx.send('OH NO ERROR: {}'.format(str(e)))
                else:
                    song = Song(source)

                    await ctx.voice_state.songs.put(song)
                    await ctx.send('Enqueued {}'.format(str(source)))
                    await ctx.message.add_reaction('🎶')
 
   
   
   
   
    @commands.command(name='ping')
    async def ping(ctx):
      """ Pong! """
      await delete_message(ctx.message)
      before = time.monotonic()
      message = await ctx.send("Pong!")
      ping = (time.monotonic() - before) * 1000
      await message.edit(content=f"Pong!  `{int(ping)}ms`")
      print(f'Ping {int(ping)}ms')
    
    
    
    
    
    
    @join.before_invoke
    @play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('FIRST CONNECT TO A VOICE CHANNEL')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Already in a voice channel')


bot = commands.Bot('.', description='sids music bot')
bot.add_cog(Music(bot))


@bot.event
async def on_ready():
    print('Logged in as:\n{0.user.name}\n{0.user.id}'.format(bot))

bot.run(token)
