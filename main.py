import asyncio
import async_timeout
import copy
import datetime
import discord
import math
import random
import re
import typing
import wavelink
import json
import spotipy
import os
import time
import threading
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands, menus
os.environ["SPOTIPY_CLIENT_ID"] = 'YOUR__CLIENT_ID'
os.environ["SPOTIPY_CLIENT_SECRET"] = 'YOUR__CLIENT_SECRET'
URL_REG = re.compile(r'https?://(?:www\.)?.+')


def run_lavalink():
  os.system("java -jar Lavalink.jar")

threading.Thread(target=run_lavalink).start()
time.sleep(100)



class NoChannelProvided(commands.CommandError):
    pass
class IncorrectChannelError(commands.CommandError):
    pass
class Track(wavelink.Track):

    __slots__ = ('requester',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.requester = kwargs.get('requester')


class Player(wavelink.Player):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.context: commands.Context = kwargs.get('context', None)
        if self.context:
            self.dj: discord.Member = self.context.author

        self.queue = asyncio.Queue()
        self.controller = None
        self.waiting = False
        self.updating = False
        self.bot=bot
        self._song=''
        self._loops = False
        self._loopq = False
        self.pause_votes = set()
        self.resume_votes = set()
        self.skip_votes = set()
        self.shuffle_votes = set()
        self.stop_votes = set()
    @property
    def song(self):
        return self._song
    @song.setter
    def song(self,value: str):
      self._song= value
    @property
    def loops(self):
        return self._loops
    @loops.setter
    def loops(self, value: bool):
        self._loops = value
    @property
    def loopq(self):
        return self._loopq
    @loopq.setter
    def loopq(self, value: bool):
        self._loopq = value
    def build_embed(self) -> typing.Optional[discord.Embed]:
     track = self.current
     if not track:
            return
     b="https://img.youtube.com/vi/"+str(track.ytid)+"/maxresdefault.jpg"
     if self.is_paused == False:
      if self.loops == True:
        track = self.current
        if not track:
            return
        c = track.title
        channel = self.bot.get_channel(int(self.channel_id))

        embed = (discord.Embed(title='Now playing',
                               description='```css\n' + c + '\n```',
                               color=discord.Color.default()))
        embed.add_field(name='Duration', value=str(datetime.timedelta(milliseconds=int(track.length))))
        embed.add_field(name='Artist', value=track.author)
        embed.add_field(name='URL', value=f'[Click]({track.uri})')
        embed.set_image(url=b)
        embed.set_footer(text="Song: Playing▶ | Loop state: Looping the current track")
        return embed
      elif self.loopq == True:
        track = self.current
        if not track:
            return
        c = track.title
        channel = self.bot.get_channel(int(self.channel_id))

        embed = (discord.Embed(title='Now playing',
                               description='```css\n' + c + '\n```',
                               color=discord.Color.default()))
        embed.add_field(name='Duration', value=str(datetime.timedelta(milliseconds=int(track.length))))
        embed.add_field(name='Artist', value=track.author)
        embed.add_field(name='URL', value=f'[Click]({track.uri})')
        embed.set_image(url=b)
        embed.set_footer(text="Song: Playing▶ | Loop state: Looping the queue")
        return embed
      else:
        track = self.current
        if not track:
            return
        c = track.title
        channel = self.bot.get_channel(int(self.channel_id))

        embed = (discord.Embed(title='Now playing',
                               description='```css\n' + c + '\n```',
                               color=discord.Color.default()))
        embed.add_field(name='Duration', value=str(datetime.timedelta(milliseconds=int(track.length))))
        embed.add_field(name='Artist', value=track.author)
        embed.add_field(name='URL', value=f'[Click]({track.uri})')
        embed.set_image(url=b)
        embed.set_footer(text="Song: Playing▶ | Loop state: Not looping")
        return embed
     else:
      try:
       if self.loops == True:
        track = self.current
        if not track:
            return
        c = track.title
        channel = self.bot.get_channel(int(self.channel_id))

        embed = (discord.Embed(title='Now playing',
                               description='```css\n' + c + '\n```',
                               color=discord.Color.default()))
        embed.add_field(name='Duration', value=str(datetime.timedelta(milliseconds=int(track.length))))
        embed.add_field(name='Artist', value=track.author)
        embed.add_field(name='URL', value=f'[Click]({track.uri})')
        embed.set_image(url=b)
        embed.set_footer(text="Song: Paused⏸️ | Loop state: Looping the current track")
        return embed
       elif self.loopq == True:
        track = self.current
        if not track:
            return
        c = track.title
        channel = self.bot.get_channel(int(self.channel_id))

        embed = (discord.Embed(title='Now playing',
                               description='```css\n' + c + '\n```',
                               color=discord.Color.default()))
        embed.add_field(name='Duration', value=str(datetime.timedelta(milliseconds=int(track.length))))
        embed.add_field(name='Artist', value=track.author)
        embed.add_field(name='URL', value=f'[Click]({track.uri})')
        embed.set_image(url=b)
        embed.set_footer(text="Song: Paused⏸️ | Loop state: Looping the queue")
        return embed
       else:
        track = self.current
        if not track:
            return
        c = track.title
        channel = self.bot.get_channel(int(self.channel_id))

        embed = (discord.Embed(title='Now playing',
                               description='```css\n' + c + '\n```',
                               color=discord.Color.default()))
        embed.add_field(name='Duration', value=str(datetime.timedelta(milliseconds=int(track.length))))
        embed.add_field(name='Artist', value=track.author)
        embed.add_field(name='URL', value=f'[Click]({track.uri})')
        embed.set_image(url=b)
        embed.set_footer(text="Song: Paused⏸️ | Loop state: Not looping")
        return embed
      except Exception as e:
        print(e)
    async def do_next(self) -> None:
        if self.is_playing or self.waiting:
            return

        self.pause_votes.clear()
        self.resume_votes.clear()
        self.skip_votes.clear()
        self.shuffle_votes.clear()
        self.stop_votes.clear()

        with open("tracks.json","r") as f:
          d=json.load(f)
        x=d.get(str(self.guild_id))
        if x==None:
          print("nice")
        elif x ==[]:
          print('nice')
        else:
            player: Player = self.bot.wavelink.get_player(self.context.guild.id, cls=Player, context=self.context)
            query=x.pop(0)
            h=query
            query = query.strip('<>')
            if not URL_REG.match(query):
                          query = f'ytsearch:{query}'
            tracks = await self.bot.wavelink.get_tracks(query)
            if not tracks:
                o="An error occurred while playing " +h
                await self.context.send(o,delete_after=5)
                with open("tracks.json","r") as f:
                    d=json.load(f)
                d[str(self.guild_id)] = x
                with open("tracks.json","w") as f:
                    json.dump(d,f)
                return await player.do_next()
            track = Track(tracks[0].id, tracks[0].info, requester=self.context.author)
            await self.play(track)
            self.waiting = False
            with open("tracks.json","r") as f:
                d=json.load(f)
            d[str(self.guild_id)] = x
            with open("tracks.json","w") as f:
                json.dump(d,f)
            with open("premium.json", 'r') as j:
                d = json.load(j)
            g = str(self.context.guild.id)
            for i in d:
                if g == i:
                    channel = bot.get_channel(d.get(str(i))[5])
                    me = d.get(str(i))[0]
                    message = await channel.fetch_message(me)
            try:
              await message.edit(embed=self.build_embed())
            except:
              time.sleep(5)
              await message.edit(embed=self.build_embed())
        if self.loopq == True:
              with open("tracks.json","r") as f:
                d=json.load(f)
              y=d.get(str(self.guild_id))
              y.append(h)
              d[str(self.guild_id)] = y
              with open("tracks.json","w") as f:
                json.dump(d,f)


class PaginatorSource(menus.ListPageSource):

    def __init__(self, entries, *, per_page=10):
        super().__init__(entries, per_page=per_page)

    async def format_page(self, menu: menus.Menu, page):
        embed = discord.Embed(title='Queue', colour=discord.Color.default())
        embed.description = '\n'.join(f'`{index}. {title}`' for index, title in enumerate(page, 1))

        return embed

    def is_paginating(self):
        return True
class PaginatorSource2(menus.ListPageSource):

    def __init__(self, entries, *, per_page=10):
        super().__init__(entries, per_page=per_page)

    async def format_page(self, menu: menus.Menu, page):
        embed = discord.Embed(title='Favourites', colour=discord.Color.default())
        embed.description = '\n'.join(f'`{index}. {title}`' for index, title in enumerate(page, 1))
        return embed

    def is_paginating(self):
        return True


class Music(commands.Cog, wavelink.WavelinkMixin):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        if not hasattr(bot, 'wavelink'):
            bot.wavelink = wavelink.Client(bot=bot)

        bot.loop.create_task(self.start_nodes())

    async def start_nodes(self) -> None:
        await self.bot.wait_until_ready()
        if self.bot.wavelink.nodes:
            previous = self.bot.wavelink.nodes.copy()

            for node in previous.values():
                await node.destroy()

        nodes = {'MAIN': {'host': '0.0.0.0',
                          'port': 5000,
                          'rest_uri': 'http://0.0.0.0:5000',
                          'password': 'youshallnotpass',
                          'identifier': 'MAIN',
                          'region': 'us_central'
                          }}

        for n in nodes.values():
            await self.bot.wavelink.initiate_node(**n)
        
        with open("premium.json", 'r') as j:
                        d = json.load(j)
        for i in d:
              channel = bot.get_channel(d.get(str(i))[5])
              message = await channel.fetch_message(d.get(str(i))[0])
              ctx = await bot.get_context(message)
              player: Player = bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
              await player.connect(d.get(str(i))[4])

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node: wavelink.Node):
        print(f'Node {node.identifier} is ready!')

    @wavelink.WavelinkMixin.listener('on_track_stuck')
    @wavelink.WavelinkMixin.listener('on_track_end')
    @wavelink.WavelinkMixin.listener('on_track_exception')
    async def on_player_stop(self, node: wavelink.Node, payload: wavelink.events.TrackEnd):
      if payload.player.loops == False:
        with open("premium.json", 'r') as j:
                d = json.load(j)
        g = str(payload.player.guild_id)
        embed = discord.Embed(title='Player',
                              description='Not playing any music right now',
                              color=discord.Color.default())
        for i in d:
                  if g == i:
                    me = d.get(str(i))[0]
                    channel = bot.get_channel(d.get(str(i))[5])     
                    message = await channel.fetch_message(me)
                    await message.edit(embed=embed)  
        await payload.player.do_next()
      else:
        query=str(payload.player.song)
        print(query)
        query = query.strip('<>')
        print(query)
        player=payload.player
        print(query)
        try:
                      if not URL_REG.match(query):
                          query = f'ytsearch:{query}'

                      tracks = await self.bot.wavelink.get_tracks(query)
                      track = Track(tracks[0].id, tracks[0].info, requester=None)
                      await player.play(track)
        except Exception as e:
          print(e)
          print("nice")
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        if member.bot:
            return

        player: Player = self.bot.wavelink.get_player(member.guild.id, cls=Player)

        if not player.channel_id or not player.context:
            player.node.players.pop(member.guild.id)
            return

        channel = self.bot.get_channel(int(player.channel_id))

        if member == player.dj and after.channel is None:
            for m in channel.members:
                if m.bot:
                    continue
                else:
                    player.dj = m
                    return

        elif after.channel == channel and player.dj not in channel.members:
            player.dj = member

    async def cog_command_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, IncorrectChannelError):
            return

        if isinstance(error, NoChannelProvided):
            return await ctx.send('You must be in a voice channel or provide one to connect to.')

    async def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            await ctx.send('Music commands are not available in Private Messages.')
            return False

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        player: Player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player, context=ctx)
        if ctx.command.name == 'connect' and not player.context:
            return
        elif self.is_privileged(ctx):
            return

        if not player.channel_id:
            return

        channel = self.bot.get_channel(int(player.channel_id))
        if not channel:
            return

        if player.is_connected:
            if ctx.author not in channel.members:
                await ctx.send(f'{ctx.author.mention}, you must be in `{channel.name}` to use voice commands.')
                raise IncorrectChannelError

    def required(self, ctx: commands.Context):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        channel = self.bot.get_channel(int(player.channel_id))
        required = math.ceil((len(channel.members) - 1) / 2.5)

        if ctx.command.name == 'stop':
            if len(channel.members) == 3:
                required = 2

        return required

    def is_privileged(self, ctx: commands.Context):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        return player.dj == ctx.author or ctx.author.guild_permissions.kick_members

    @commands.command(name='join', aliases=["connect"])
    async def connect(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        if player.is_connected:
            return
        channel = getattr(ctx.author.voice, 'channel', channel)
        if channel is None:
            raise NoChannelProvided
        await player.connect(channel.id)
    @commands.command(aliases=['p'])
    async def play(self, ctx: commands.Context, *, query: str):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        if not player.is_connected:
            await ctx.invoke(self.connect)
        try:
            if "spotify" in query:
                g = str(ctx.guild.id)
                search = query
                client_credentials_manager = SpotifyClientCredentials()
                sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
                if "spotify" and "track" in str(search):
                      track = str(search)
                      res = sp.track(track)
                      song = res['name']
                      artist = res['artists'][0]['name']
                      songToPlay = str(song) + "-" + str(artist)
                      query=songToPlay 
                      query = query.strip('<>')
                      if not URL_REG.match(query):
                            query = f'ytsearch:{query}'

                      tracks = await self.bot.wavelink.get_tracks(query)
                      if not tracks:
                          return await ctx.send('No songs were found with that query. Please try again.', delete_after=5)
                      else:
                          track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
                          await ctx.send(f'```ini\nAdded {track.title} to the Queue\n```', delete_after=5)
                          with open("tracks.json","r") as f:
                            d=json.load(f)
                          x=d.get(str(ctx.guild.id))
                          if x== None:
                             x=[str(track.title)]
                          else:
                             x=x+[str(track.title)]
                          d[str(ctx.guild.id)]=x
                          with open("tracks.json","w") as f:
                            json.dump(d,f)
                      if not player.is_playing:
                          await player.do_next()
                elif ".spotify" and "playlist" in str(search):
                        def get_playlist_tracks(playlist_id):
                            results = sp.playlist_tracks(playlist_id)
                            tracks = results['items']
                            while results['next']:
                                results = sp.next(results)
                                tracks.extend(results['items'])
                            return tracks
                        playlist = str(search)
                        res2 = get_playlist_tracks(playlist)
                        x = sp.playlist_cover_image(playlist)[0]
                        ser = sp.playlist(playlist, fields="name")
                        d = str(ser["name"])
                        y = x.get('url')
                        l = str(len(res2))
                        f = '[Click](' + playlist + ')'
                        embed = (discord.Embed(title='Queued' + ' ' + l + ' ' + 'tracks',
                                               description='',
                                               color=discord.Color.green())
                                 .add_field(name='Playlist Name', value=d)
                                 .add_field(name='Playlist Link', value=f.format(self=playlist))
                                 .set_thumbnail(url='https://developer.spotify.com/assets/branding-guidelines/icon3@2x.png')
                                 .set_image(url=y))                  
                        await ctx.send(embed=embed,delete_after=15)
                        with open("tracks.json","r") as f:
                            d=json.load(f)
                        x=d.get(str(ctx.guild.id))
                        for items in res2:
                            song = str(items["track"]["name"])
                            artist = str(items["track"]["artists"][0]["name"])
                            songToPlay = str(song) + " " + str(artist)
                            if not player.is_playing:
                                songToPlay = songToPlay.strip('<>')
                                if not URL_REG.match(songToPlay):
                                    songToPlay = f'ytsearch:{songToPlay}'
                                tracks = await self.bot.wavelink.get_tracks(songToPlay)
                                if not tracks:
                                    continue
                                track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
                                if x == None:
                                  x=[str(track.title)]
                                else:
                                  x=x+[str(track.title)]
                                d[str(ctx.guild.id)]=x
                                with open("tracks.json","w") as f:
                                    json.dump(d,f)
                                await player.do_next()
                                x.pop(0)
                            else:
                              x=x+[songToPlay]
                              d[str(ctx.guild.id)]=x
                              with open("tracks.json","w") as f:
                                    json.dump(d,f)
                elif ".spotify" and "album" in str(search):
                        def get_album_tracks(album_id):
                            results = sp.album_tracks(album_id)
                            tracks = results['items']
                            while results['next']:
                                results = sp.next(results)
                                tracks.extend(results['items'])
                            return tracks
                        album = str(search)
                        res2 = get_album_tracks(album)
                        ser = sp.album(album)
                        x = str(ser.get('images')[0].get('url'))
                        d = str(ser.get('name'))
                        l = str(len(res2))
                        f = '[Click](' + album + ')'
                        embed = (discord.Embed(title='Queued' + ' ' + l + ' ' + 'tracks',
                                               description='',
                                               color=discord.Color.green())
                                 .add_field(name='Album Name', value=d)
                                 .add_field(name='Album Link', value=f.format(self=album))
                                 .set_thumbnail(url='https://developer.spotify.com/assets/branding-guidelines/icon3@2x.png')
                                 .set_image(url=x)
                                 )                       
                        await ctx.send(embed=embed,delete_after=15)
                        with open("tracks.json","r") as f:
                            d=json.load(f)
                        x=d.get(str(ctx.guild.id))
                        for items in res2:
                            song = items["name"]
                            artist = items["artists"][0]["name"]
                            songToPlay = str(song) + " " + str(artist)
                            if not player.is_playing:
                                songToPlay = songToPlay.strip('<>')
                                if not URL_REG.match(songToPlay):
                                    songToPlay = f'ytsearch:{songToPlay}'
                                tracks = await self.bot.wavelink.get_tracks(songToPlay)
                                if not tracks:
                                    continue
                                track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
                                if x == None:
                                  x=[str(track.title)]
                                else:
                                  x=x+[str(track.title)]
                                d[str(ctx.guild.id)]=x
                                with open("tracks.json","w") as f:
                                    json.dump(d,f)
                                await player.do_next()
                                x.pop(0)
                            else:
                              x=x+[songToPlay]
                              d[str(ctx.guild.id)]=x
                              with open("tracks.json","w") as f:
                                    json.dump(d,f)
            else:
                      query = query.strip('<>')
                      if not URL_REG.match(query):
                          query = f'ytsearch:{query}'

                      tracks = await self.bot.wavelink.get_tracks(query)
                      if not tracks:
                          return await ctx.send('No songs were found with that query. Please try again.', delete_after=5)
                      if isinstance(tracks, wavelink.TrackPlaylist):
                          for track in tracks.tracks:
                              track = Track(track.id, track.info, requester=ctx.author)
                              with open("tracks.json","r") as f:
                                    d=json.load(f)
                              x=d.get(str(ctx.guild.id))
                              if x== None:
                                 x=[str(track.uri)]
                              else:
                                   x=x+[str(track.uri)]
                              d[str(ctx.guild.id)]=x
                              with open("tracks.json","w") as f:
                                 json.dump(d,f)
                          x='#FF0000'
                          sixteenIntegerHex = int(x.replace("#", ""), 16)
                          h = int(hex(sixteenIntegerHex), 0)
                          embed=(discord.Embed(title=f'Queued the playlist {tracks.data["playlistInfo"]["name"]}'
                                       f' with {len(tracks.tracks)} songs to the queue.',description='',color=h))
                          await ctx.send(embed=embed,delete_after=15)                               
                      else:
                          track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
                          await ctx.send(f'```ini\nAdded {track.title} to the Queue\n```', delete_after=5)
                          with open("tracks.json","r") as f:
                            d=json.load(f)
                          x=d.get(str(ctx.guild.id))
                          if x== None:
                             x=[str(track.title)]
                          else:
                             x=x+[str(track.title)]
                          d[str(ctx.guild.id)]=x
                          with open("tracks.json","w") as f:
                            json.dump(d,f)
                      if not player.is_playing:
                          await player.do_next()
        except Exception as e:
            print(e)

    @commands.command(aliases=['v', 'vol'])
    async def volume(self, ctx: commands.Context, *, vol: int):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if not 0 < vol < 101:
            return await ctx.send('Please enter a value between 1 and 100.',delete_after=7)

        await player.set_volume(vol)
        await ctx.send(f'Set the volume to **{vol}**%', delete_after=7)
    @commands.command(aliases=['eq'])
    async def equalizer(self, ctx: commands.Context, *, equalizer: str):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        eqs = {'flat': wavelink.Equalizer.flat(),
               'boost': wavelink.Equalizer.boost(),
               'metal': wavelink.Equalizer.metal(),
               'piano': wavelink.Equalizer.piano()}

        eq = eqs.get(equalizer.lower(), None)

        if not eq:
            joined = "\n".join(eqs.keys())
            return await ctx.send(f'Invalid EQ provided. Valid EQs:\n\n{joined}',delete_after=7)

        await ctx.send(f'Successfully changed equalizer to {equalizer}', delete_after=5)
        await player.set_eq(eq)
    @commands.command(name='remove')
    async def cancel(self, ctx: commands.Context,tr:int):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        with open("tracks.json","r") as f:
                          d=json.load(f)
        x=d.get(str(ctx.guild.id))
        if x== None:
          return await ctx.send("Empty Queue",delete_after=5)
        elif x == []:
          return await ctx.send("Empty Queue",delete_after=5)
        x.pop(tr-1)
        d[str(ctx.guild.id)]=x
        with open("tracks.json","w") as f:
          json.dump(d,f)
        o="Removed track" +" " + str(tr)
        await ctx.send(o,delete_after=5)
    @commands.command(name='queue',aliases=['q'])
    async def queue(self, ctx: commands.Context):
      try:
        with open("tracks.json","r") as f:
            d=json.load(f)
        x=d.get(str(ctx.guild.id))
        if x == None:
            return await ctx.send('There are no more songs in the queue.', delete_after=5)
        elif x == []:
            return await ctx.send('There are no more songs in the queue.', delete_after=5)
        else:
              entries = x
              pages = PaginatorSource(entries=entries)
              paginator = menus.MenuPages(source=pages, timeout=None, delete_message_after=30)
              await paginator.start(ctx)
      except Exception as e:
        print(e)
    @commands.command(name='favourites')
    async def fav(self, ctx: commands.Context):
      with open("fav.json","r") as f:
          u=json.load(f)
      h=str(ctx.author.id)
      x=u.get(h)     
      if x == None:
        await ctx.send("You haven't set any tracks as your favourite,set the currently playing track as one of your favourites by pressing 🌟",delete_after=5)
      else:
        pages = PaginatorSource2(entries=x)
        paginator2 = menus.MenuPages(source=pages, timeout=None, delete_message_after=30) 
        await paginator2.start(ctx)
    @commands.command(aliases=['ff', 'forward'])
    async def fastforward(self, ctx: commands.Context, *, pos: int):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        c=player.position
        if c==0:
          await ctx.send("currently no music is being played",delete_after=5)
        else:
          y=str(pos)
          position=pos*1000
          position=c+position
          await player.seek(position)
          o="Skipped "+y+" seconds"
          await ctx.send(o,delete_after=5)
    @commands.command(aliases=['back'])
    async def rewind(self, ctx: commands.Context, *, pos: int):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        c=player.position
        if c==0:
          await ctx.send("currently no music is being played",delete_after=5)
        else:
          y=str(pos)
          position=pos*1000
          position=c - position
          if position>0:
            await player.seek(position)
            o="Rewinded "+y+" seconds"
            await ctx.send(o,delete_after=5)
          else:
            position=0
            await player.seek(position)
            await ctx.send("Rewinded to the beginning",delete_after=5)
    @commands.command(name='setchannel')
    @commands.has_permissions(administrator=True)
    async def setchannel(self, ctx: commands.Context):
        embed2 = (discord.Embed(title='',
                                description='',
                                color=discord.Color.default())
            .set_image(
            url='https://66.media.tumblr.com/065a900f9d11bc67b628a3ea72d8f52b/tumblr_piwzvf6QzN1vf8r3co1_1280.gif')
        )
        embed = discord.Embed(title='Player',
                              description='Not playing any music right now',
                              color=discord.Color.default())
        await ctx.send(embed=embed2)
        message = await ctx.send(embed=embed)
        await message.add_reaction('▶️')
        await message.add_reaction('⏸️')
        await message.add_reaction('⏭')
        await message.add_reaction('🛑')
        await message.add_reaction('🔀')
        await message.add_reaction('🔁')
        await message.add_reaction('➿')
        await message.add_reaction('🌟')
        m = str(ctx.guild.id)
        r = [message.id,123,"ok","okok", ctx.author.voice.channel.id,ctx.channel.id]
        chj=self.bot.get_channel(ctx.channel.id)
        await chj.edit(topic='HELP: use the  volume command to change the volume,⏯-Play or Resume,⏭-skips the current track,🛑-Stops the song and clears the queue,🔀-Shuffles the queue,🔁-loops the current track,➿-loops the queue,press 🌟 to set the surrent track as one of your favourites,use the favourites command to view your favourite tracks and use fav followed the number of your favourite song to play it',slowmode_delay=2)
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        await player.connect(ctx.author.voice.channel.id)
        with open("premium.json") as json_file:
            json_decoded = json.load(json_file)
        json_decoded[m] = r
        with open("premium.json", 'w') as json_file:
            json.dump(json_decoded, json_file)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', description='sids music bot',
                   help_command=None, Intents=intents)
bot.add_cog(Music(bot))
@bot.event
async def on_raw_reaction_add(payload):
  i=payload.message_id
  channel = bot.get_channel(payload.channel_id)
  message = await channel.fetch_message(i)
  if str(message.author.id) == str(bot.user.id):
    if str(payload.user_id) != str(bot.user.id):
      if payload.member.voice == None:
        with open("premium.json", 'r') as j:
                                  d = json.load(j)
        g = str(payload.guild_id)
        for i in d:
                                if g == i:
                                  me = d.get(str(i))[0]
                                  channel = bot.get_channel(d.get(str(i))[5])
                                  message = await channel.fetch_message(me)
                                  await message.remove_reaction(emoji=payload.emoji,member=payload.member)
        ch = bot.get_channel(payload.channel_id)
        return await ch.send("First connect to a voice channel",delete_after=5)
      else:
        if str(payload.user_id) != str(bot.user.id):
          emoji =str(payload.emoji)
          i=payload.message_id
          channel = bot.get_channel(payload.channel_id)
          message = await channel.fetch_message(i)
          ctx = await bot.get_context(message)
          player: Player = bot.wavelink.get_player(guild_id=payload.guild_id, cls=Player,context=ctx)
          if payload.member.voice.channel.id != player.channel_id:
            with open("premium.json", 'r') as j:
                                  d = json.load(j)
            g = str(payload.guild_id)
            for i in d:
                                if g == i:
                                  me = d.get(str(i))[0]
                                  channel = bot.get_channel(d.get(str(i))[5])
                                  message = await channel.fetch_message(me)
                                  await message.remove_reaction(emoji=emoji,member=payload.member)
            return await ctx.send("You have to be in the same voice channel as crescendo ultimate to use this command",delete_after=5)
          else:
              try:
                b=player.position
                if b == 0:
                  with open("premium.json", 'r') as j:
                                  d = json.load(j)
                  g = str(payload.guild_id)
                  for i in d:
                                if g == i:
                                  me = d.get(str(i))[0]
                                  channel = bot.get_channel(d.get(str(i))[5])
                                  message = await channel.fetch_message(me)
                                  await message.remove_reaction(emoji=emoji,member=payload.member)
                  await ctx.send("Currently No music is being played",delete_after=5)
                else:
                      if emoji == '🌟':
                          with open("fav.json","r") as f:
                            u=json.load(f)
                          h=str(payload.user_id)
                          x=u.get(h)
                          if player.current == None:
                              await ctx.send("No music is playing right now",delete_after=5)
                          elif x == None:  
                              z=str(player.current.title)          
                              user="<@"+h+">"
                              miss="I've set"+" "+z+" "+"as your favourite track"+" "+user
                              await ctx.send(miss,delete_after=5)
                              x=[]
                              z=[str(player.current.title)]
                              u[h]= z+x
                              with open("fav.json","w") as f:
                                json.dump(u,f)
                          else:
                              z=str(player.current.title)
                              user="<@"+h+">"
                              miss="I've Set"+" "+z+" "+"as your favourite track"+" "+user
                              await ctx.send(miss,delete_after=5)
                              z=[str(player.current.title)]
                              u[h]= z+x
                              with open("fav.json","w") as f:
                                json.dump(u,f)
                      elif emoji=='🛑':
                              with open("tracks.json","r") as f:
                                      d=json.load(f)
                              d[str(payload.guild_id)]=[]
                              with open("tracks.json","w") as f:
                                      json.dump(d,f)
                              await player.stop()
                              player.loops =False
                              player.loopq == False
                              player.song = ''
                              await player.set_pause(False)
                              embed6=discord.Embed(title='Loop State', description='Not looping', color=discord.Color.default())
                              with open("premium.json", 'r') as j:
                                      d = json.load(j)
                              g = str(payload.guild_id)
                              for i in d:
                                    if g == i:
                                      mee = d.get(str(i))[0]
                                      channel = bot.get_channel(d.get(str(i))[5]) 
                                      message = await channel.fetch_message(mee)
                                      await message.edit(embed=embed6)
                      elif emoji=="▶️":
                          await player.set_pause(False)
                          try:
                              with open("premium.json", 'r') as j:
                                  d = json.load(j)
                              g = str(payload.guild_id)
                              for i in d:
                                if g == i:
                                  me = d.get(str(i))[0]
                                  channel = bot.get_channel(d.get(str(i))[5])
                                  message = await channel.fetch_message(me)
                                  await message.edit(embed=player.build_embed())
                              with open("premium.json", 'r') as j:
                                  d = json.load(j)
                              g = str(payload.guild_id)
                              for i in d:
                                if g == i:
                                  me = d.get(str(i))[0]
                                  channel = bot.get_channel(d.get(str(i))[5])        
                                  message = await channel.fetch_message(me)
                                  await message.remove_reaction(emoji=emoji,member=payload.member)
                          except Exception as e:
                              print(e)
                      elif emoji=="⏸️":
                          await player.set_pause(True)
                          try:
                              with open("premium.json", 'r') as j:
                                  d = json.load(j)
                              g = str(payload.guild_id)
                              for i in d:
                                if g == i:
                                  me = d.get(str(i))[0]
                                  channel = bot.get_channel(d.get(str(i))[5])        
                                  message = await channel.fetch_message(me)
                                  await message.edit(embed=player.build_embed())
                              with open("premium.json", 'r') as j:
                                  d = json.load(j)
                              g = str(payload.guild_id)
                              for i in d:
                                if g == i:
                                  me = d.get(str(i))[0]
                                  channel = bot.get_channel(d.get(str(i))[5])        
                                  message = await channel.fetch_message(me)
                                  await message.remove_reaction(emoji=emoji,member=payload.member)
                              
                          except Exception as e:
                              print(e)
                      elif emoji=="⏭":
                              await player.stop()
                      elif emoji=="🔀":
                              with open("tracks.json","r") as f:
                                      d=json.load(f)
                              x=d.get(str(payload.guild_id))
                              random.shuffle(x)
                              d[str(payload.guild_id)]=x
                              with open("tracks.json","w") as f:
                                      json.dump(d,f)
                              await ctx.send("Queue Shuffled",delete_after=5)
                      elif emoji=="➿":
                          b=player.position
                          if b == 0:
                            await ctx.send("Currently no music is being played",delete_after=5)
                          else:
                            player.loops =False
                            if player.loopq == True:
                              player.loopq = False
                              player.song = ''
                              with open("premium.json", 'r') as j:
                                      d = json.load(j)
                              g = str(payload.guild_id)
                              for i in d:
                                    if g == i:
                                      mee = d.get(str(i))[0]
                                      channel = bot.get_channel(d.get(str(i))[5])        
                                      message = await channel.fetch_message(mee)
                                      await message.edit(embed=player.build_embed())
                            else:
                              player.loopq = True
                              with open("premium.json", 'r') as j:
                                      d = json.load(j)
                              g = str(payload.guild_id)
                              for i in d:
                                    if g == i:
                                      mee = d.get(str(i))[0]
                                      channel = bot.get_channel(d.get(str(i))[5])        
                                      message = await channel.fetch_message(mee)
                                      await message.edit(embed=player.build_embed())
                              with open("tracks.json","r") as f:
                                      d=json.load(f)
                              y=d.get(str(payload.guild_id))
                              h=str(player.current.uri)
                              y.append(h)
                              d[str(payload.guild_id)] = y
                              with open("tracks.json","w") as f:
                                      json.dump(d,f)
                        
                      elif emoji=="🔁":
                          b=player.position
                          if b == 0:
                            await ctx.send("Currently no music is being played",delete_after=5)
                          else:
                            player.loopq =False
                            if player.loops == True:
                              player.loops = False
                              player.song = ''
                              with open("premium.json", 'r') as j:
                                      d = json.load(j)
                              g = str(payload.guild_id)
                              for i in d:
                                    if g == i:
                                      mee = d.get(str(i))[0]
                                      channel = bot.get_channel(d.get(str(i))[5])        
                                      message = await channel.fetch_message(mee)
                                      await message.edit(embed=player.build_embed())
                            else:
                              player.loops = True
                              player.song = player.current
                              with open("premium.json", 'r') as j:
                                      d = json.load(j)
                              g = str(payload.guild_id)
                              for i in d:
                                    if g == i:
                                      mee = d.get(str(i))[0]
                                      channel = bot.get_channel(d.get(str(i))[5])        
                                      message = await channel.fetch_message(mee)
                                      await message.edit(embed=player.build_embed())
                      else:
                            print("ok")
                      with open("premium.json", 'r') as j:
                                  d = json.load(j)
                      g = str(payload.guild_id)
                      for i in d:
                                if g == i:
                                  me = d.get(str(i))[0]
                                  channel = bot.get_channel(d.get(str(i))[5])        
                                  message = await channel.fetch_message(me)
                                  await message.remove_reaction(emoji=emoji,member=payload.member)
              except Exception as e:
                      print(e)
@bot.event
async def on_message(message):
  if message.content.lower() == '.setchannel':
    await bot.process_commands(message)
    await message.delete()
  elif message.content.lower() == '.favourites':
    await bot.process_commands(message)
    await message.delete()
  elif '.fav' in message.content.lower():
    ctx = await bot.get_context(message)
    player: Player = bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
    t=str(message.content)
    t=t.replace(".fav","")
    t=int(t)-1
    try:
              with open("fav.json","r") as f:
                u=json.load(f)
              query=u.get(str(ctx.message.author.id))
              query=str(query[t])
              query = query.strip('<>')
              if not URL_REG.match(query):
                              query = f'ytsearch:{query}'

                              tracks = await bot.wavelink.get_tracks(query)
              if not tracks:
                                  return await ctx.send('No songs were found with that query. Please try again.', delete_after=5)
              else:
                          track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
                          await ctx.send(f'```ini\nAdded {track.title} to the Queue\n```', delete_after=5)
                          with open("tracks.json","r") as f:
                            d=json.load(f)
                          x=d.get(str(ctx.guild.id))
                          if x== None:
                             x=[str(track.title)]
                          else:
                             x=x+[str(track.title)]
                          d[str(ctx.guild.id)]=x
                          with open("tracks.json","w") as f:
                            json.dump(d,f)

              if not player.is_playing:
                                  await player.do_next()
    except Exception as e:
        print(e)
        await ctx.send("You haven't set any track as your favourite or haven't provided a valid argument",delete_after=5)
    await message.delete()
  elif str(message.guild.id) == '': #fill the quotations with the channel id you want the bot to be in
    if message.content.lower().startswith('.'):
      await bot.process_commands(message)
  else:
   ctx = await bot.get_context(message)
   if str(ctx.author.id) != str(bot.user.id):
     g=str(message.guild.id)
     with open("premium.json", 'r') as j:
                d = json.load(j)
     ch=''
     for i in d:
        if g==i:
          ch = bot.get_channel(d.get(i)[5])
     if message.content.lower().startswith('.'):
          if message.channel.id == ch.id:
                 try:
                    await bot.process_commands(message)
                    await message.delete()
                 except Exception as e:
                    print(e)

          else:
             print("ok")
     elif message.channel.id == ch.id:
        await message.delete()
     else:
          print("ok")
@bot.event
async def on_ready():
 print('Logged in as:\n{0.user.name}\n{0.user.id}'.format(bot))
 await bot.change_presence(activity=activityvar, status=discord.Status.idle) 
 g=bot.get_guild() #fill the brackets with your guild's id
 await g.leave()
 with open("tracks.json","r") as f:
              d=json.load(f)
 for i in d:
      d[str(i)]=[]
      with open("tracks.json","w") as f:
                    json.dump(d,f)         
bot.run('YOUR_BOT_TOKEN')
