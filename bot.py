import discord
from discord import FFmpegPCMAudio
from discord.ext import commands
from urllib.parse import urlparse, parse_qs
from colorama import Fore, Style
import json
import asyncio
import yt_dlp


from Song import Song
from Playlist import Playlist


TOKEN = ""
PREFIX = ""
YTDL_OPTIONS = {}
FFMPEG_OPTIONS = {}

with open("config.json", "r") as conf:
    conf = json.load(conf)
    TOKEN = conf["DISCORD"]["TOKEN"]
    PREFIX = conf["DISCORD"]["PREFIX"]
    YTDL_OPTIONS = conf["APP"]["YTDL_OPTIONS"]
    FFMPEG_OPTIONS = conf["APP"]["FFMPEG_OPTIONS"]



intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix=PREFIX)

songData = Song()
playlist = Playlist() 
   
    
def print_success(message: str):
    print(Fore.GREEN + f"[SUCCESS] {message}" + Style.RESET_ALL, flush=True)


def print_info(message: str):
    print(Fore.BLUE + f"[INFO] {message}" + Style.RESET_ALL, flush=True)


def print_error(message: str):
    print(Fore.RED + f"[ERROR] {message}" + Style.RESET_ALL, flush=True)


def Get_Video_Info(URL: str, id):
    video_id = urlparse(URL)
    video_id = parse_qs(video_id.query)
    video_id = video_id.get("v")
    playlist.YTDL_OPTIONS[id]["playliststart"] = playlist.playlistStart[id]
    playlist.YTDL_OPTIONS[id]["playlistend"] = playlist.playlistEnd[id]

    with yt_dlp.YoutubeDL(playlist.YTDL_OPTIONS[id]) as ydl:
        try:
            info = ydl.extract_info(URL, download=False)
            title = str(info['title']).encode("utf-8")
            print_info(f"Mendapatkan Video Info dari {title}")

            return info
        except:
            print_error("Gagal Mendapatkan Video Info")
            return None


@bot.event
async def on_ready():
    print_success("Online")
    for guild in bot.guilds:
        id = int(guild.id)
        songData.musicQueue[id] = []
        songData.queueIndex[id] = 0
        songData.vc[id] = None
        songData.autoplay[id] = False
        playlist.currentPlaylist[id] = 1
        playlist.isPlaylist[id] = False
        playlist.YTDL_OPTIONS[id] = YTDL_OPTIONS
        playlist.playlistStart[id] = 1
        playlist.playlistEnd[id] = 3


@bot.command(
    name="play",
    aliases = ["p"],
    help="Play Audio Dari Link Video Youtube"
)
async def play(ctx: commands.Context, arg: str):
    id = int(ctx.guild.id)
    url = arg
    url = urlparse(url)
    query = parse_qs(url.query)
    channel = ctx.message.author.voice.channel

    if query.get("list"):
        playlist.isPlaylist[id] = True
    else:
        playlist.isPlaylist[id] = False

    if url.netloc == "" or url.netloc != "www.youtube.com" or url.query == "":
        raise commands.ArgumentParsingError
    
    if not query.get("v"):
        raise commands.ArgumentParsingError
    
    info = Get_Video_Info(arg, id)
    if not info:
        raise commands.ArgumentParsingError

    if playlist.isPlaylist[id] == True:
        playlist.playlistURL[id] = arg
        for inf in info["entries"]:
            data = {
                "title" : inf["title"],
                "url": inf["url"]
            }
            songData.musicQueue[id].append(data)
    else:
        data = {
                "title" : info["title"],
                "url": info["url"]
            }
        songData.musicQueue[id].append(data)
    
    if songData.vc[id] == None:
        songData.vc[id] = await channel.connect(self_deaf=True)

    if songData.vc[id].is_connected() and songData.vc[id].is_playing():
        title = songData.musicQueue[id][-1]["title"]
        embed = discord.Embed(title='[Info]', 
                            description=f":information_source: Added ```{title}```",
                            color=discord.Color.blue())
        await ctx.send(embed=embed)

    if songData.vc[id].is_connected() and not songData.vc[id].is_playing():
        source = FFmpegPCMAudio(songData.musicQueue[id][songData.queueIndex[id]]["url"], **FFMPEG_OPTIONS)
        songData.vc[id].play(source)

        title = songData.musicQueue[id][songData.queueIndex[id]]["title"]
        embed = discord.Embed(title='[Info]', 
                            description=f":arrow_forward: Playing ```{title}```",
                            color=discord.Color.blue())
        await ctx.send(embed=embed)


@play.error
async def p(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title='[Error]', 
                            description=":information_source: Untuk Memutar Lagu Membutuhkan Parameter URL ```!play [URL]```" ,
                            color=discord.Color.red())
        await ctx.send(embed=embed)

    if isinstance(error, commands.ArgumentParsingError):
        embed = discord.Embed(title='[Error]', 
                            description=":information_source: Gagal Mendapatkan Audio URL, Coba Cari Menggunakan Link Lainnya" ,
                            color=discord.Color.red())
        await ctx.send(embed=embed)

    if isinstance(error, commands.UserNotFound):
        embed = discord.Embed(title='[Error]', 
                            description=":information_source: User Tidak Berada di Voice Channel" ,
                            color=discord.Color.red())
        await ctx.send(embed=embed)


@bot.command(
    name="skip",
    aliases = ["sk", "next", "nx"],
    help="Skip Audio saat ini"
)
async def skip(ctx: commands.Context):
    id = int(ctx.guild.id)

    if not (ctx.author.voice):
        raise commands.UserNotFound
    
    if songData.queueIndex[id] >= len(songData.musicQueue[id]) -1:
        try:
            playlist.playlistStart[id] += 3
            playlist.playlistEnd[id] += 3
            info = Get_Video_Info(playlist.playlistURL[id], id)
            if not info:
                raise commands.ArgumentParsingError

            if playlist.isPlaylist[id] == True:
                for inf in info["entries"]:
                    data = {
                        "title" : inf["title"],
                        "url": inf["url"]
                    }
                    songData.musicQueue[id].append(data)
        except:
            songData.vc[id].stop()
            embed = discord.Embed(title='[Info]', 
                                description=f":fast_forward: End of Playlist" ,
                                color=discord.Color.blue())
            await ctx.send(embed=embed)
        
    elif songData.queueIndex[id] < len(songData.musicQueue[id]) -1 :
        songData.queueIndex[id] += 1
        source = FFmpegPCMAudio(songData.musicQueue[id][songData.queueIndex[id]]["url"], **FFMPEG_OPTIONS)
        songData.vc[id].stop()
        songData.vc[id].play(source)

        title = songData.musicQueue[id][songData.queueIndex[id]]["title"]
        embed = discord.Embed(title='[Info]', 
                                description=f":fast_forward: Playing {title}" ,
                                color=discord.Color.blue())
        await ctx.send(embed=embed)

@skip.error
async def sk(ctx, error):
    if isinstance(error, commands.UserNotFound):
        embed = discord.Embed(title='[Error]', 
                            description=":information_source: User Tidak Berada di Voice Channel" ,
                            color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(
    name="autoplay",
    aliases = ["auto", "au"],
    help="AutoPlay Audio Dari Audio Queue"
)
async def autoplay(ctx: commands.Context):
    id = int(ctx.guild.id)

    if not (ctx.author.voice):
        raise commands.UserNotFound
    
    if songData.vc[id] == None or len(songData.musicQueue) == 0:
        raise commands.BadArgument

    desc = ""
    songData.autoplay[id] = not songData.autoplay[id]

    if songData.autoplay[id] == True:
        desc = ":information_source: Autoplay Enable"
    else:
        desc = ":information_source: Autoplay Disable"
    
    embed = discord.Embed(title='[Info]', 
                        description=desc,
                        color=discord.Color.blue())
    await ctx.send(embed=embed)

    while songData.autoplay[id]: 
        if songData.vc[id].is_playing() or songData.vc[id].is_paused():
            await asyncio.sleep(10)
            pass
        else:
            if songData.queueIndex[id] < len(songData.musicQueue[id]) -1:
                await skip(ctx)
            else:
                songData.autoplay[id] = False
                desc = ":information_source: Autoplay Disable"
                embed = discord.Embed(title='[Info]', 
                                    description=desc,
                                    color=discord.Color.blue())
                await ctx.send(embed=embed)

@autoplay.error
async def auto(ctx, error):
    if isinstance(error, commands.UserNotFound):
        embed = discord.Embed(title='[Error]', 
                            description=":information_source: User Tidak Berada di Voice Channel" ,
                            color=discord.Color.red())
        await ctx.send(embed=embed)

    if isinstance(error, commands.BadArgument):
        embed = discord.Embed(title='[Error]', 
                            description=":information_source: Tidak ada audio yang tersedia di Queue" ,
                            color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(
    name="list",
    aliases = ["ls", "lst"],
    help="List Audio Dari Audio Queue"
)
async def lst(ctx: commands.Context):
    id = int(ctx.guild.id)

    if not (ctx.author.voice):
        raise commands.UserNotFound

    if songData.vc[id] == None or len(songData.musicQueue) == 0:
        raise commands.BadArgument

    desc = ""

    for index, music in enumerate(songData.musicQueue[id], start=1):
        title = music["title"]
        if index -1 == songData.queueIndex[id]:
            desc += f"▶ {title}"
        else:
            desc += f"{index}. {title}"
        
        desc += "\n"

    embed = discord.Embed(title='[Info]', 
                        description=f":arrow_forward: Current Queue```{desc}```",
                        color=discord.Color.blue())
    await ctx.send(embed=embed)
    
@lst.error
async def ls(ctx, error):
    if isinstance(error, commands.UserNotFound):
        embed = discord.Embed(title='[Error]', 
                            description=":information_source: User Tidak Berada di Voice Channel" ,
                            color=discord.Color.red())
        await ctx.send(embed=embed)

    if isinstance(error, commands.BadArgument):
        embed = discord.Embed(title='[Error]', 
                            description=":information_source: Tidak ada audio yang tersedia di Queue" ,
                            color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(
    name="previous",
    aliases = ["prev", "pre"],
    help="Mundur Dari Audio Saat ini"
)
async def previous(ctx: commands.Context):
    id = int(ctx.guild.id)

    if not (ctx.author.voice):
        raise commands.UserNotFound
    
    if songData.queueIndex[id] == 0:
        songData.vc[id].stop()
        embed = discord.Embed(title='[Info]', 
                            description=f":rewind: End of Playlist" ,
                            color=discord.Color.blue())
        await ctx.send(embed=embed)
        
    elif songData.queueIndex[id] > 0 :
        songData.queueIndex[id] -= 1
        source = FFmpegPCMAudio(songData.musicQueue[id][songData.queueIndex[id]]["url"], **FFMPEG_OPTIONS)
        songData.vc[id].stop()
        songData.vc[id].play(source)

        title = songData.musicQueue[id][songData.queueIndex[id]]["title"]
        embed = discord.Embed(title='[Info]', 
                                description=f":rewind: Playing {title}" ,
                                color=discord.Color.blue())
        await ctx.send(embed=embed)

@previous.error
async def pre(ctx, error):
    if isinstance(error, commands.UserNotFound):
        embed = discord.Embed(title='[Error]', 
                            description=":information_source: User Tidak Berada di Voice Channel" ,
                            color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(
    name="clear",
    aliases = ["cls"],
    help="Clear Discord Bot Queue"
)
async def cls(ctx: commands.Context):
    id = int(ctx.guild.id)

    if not (ctx.author.voice):
        raise commands.UserNotFound

    songData.musicQueue[id] = []
    songData.queueIndex[id] = 0

    embed = discord.Embed(title='[Info]', 
                            description=f":x: Queue Has Been Cleared" ,
                            color=discord.Color.blue())
    await ctx.send(embed=embed)

@cls.error
async def clear(ctx, error):
    if isinstance(error, commands.UserNotFound):
        embed = discord.Embed(title='[Error]', 
                            description=":information_source: User Tidak Berada di Voice Channel" ,
                            color=discord.Color.red())
        await ctx.send(embed=embed)


@bot.command(
    name="pause",
    aliases = ["ps"],
    help="Pause Discord Bot"
)
async def pause(ctx: commands.Context):
    id = int(ctx.guild.id)

    if not (ctx.author.voice):
        raise commands.UserNotFound

    if songData.vc[id].is_playing():
        songData.vc[id].pause()
        embed = discord.Embed(title='[Info]', 
                            description=":information_source: Audio Paused" ,
                            color=discord.Color.blue())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title='[Info]', 
                            description=":information_source: Audio Play" ,
                            color=discord.Color.blue())
        await ctx.send(embed=embed)
        songData.vc[id].resume()
    
@pause.error
async def ps(ctx, error):
    if isinstance(error, commands.UserNotFound):
        embed = discord.Embed(title='[Error]', 
                            description=":information_source: User Tidak Berada di Voice Channel" ,
                            color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(
    name="exit",
    aliases = ["ex", "disconnect", "dc"],
    help="Exit Discord Bot from Voice Channel"
)
async def qt(ctx: commands.Context):
    id = int(ctx.guild.id)

    if not (ctx.author.voice):
        raise commands.UserNotFound

    if songData.vc[id] == None:
        embed = discord.Embed(title='[Error]', 
                                description=f":x: Bot Aren't on Voice Channel" ,
                                color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    if songData.vc[id].is_connected():
        await songData.vc[id].disconnect()
        songData.vc[id] = None
        songData.musicQueue[id] = []
        songData.queueIndex[id] = 0

        embed = discord.Embed(title='[Info]', 
                                description=f":x: Quit from Voice Channel" ,
                                color=discord.Color.red())
        await ctx.send(embed=embed)

@qt.error
async def qt(ctx, error):
    if isinstance(error, commands.UserNotFound):
        embed = discord.Embed(title='[Error]', 
                            description=":information_source: User Tidak Berada di Voice Channel" ,
                            color=discord.Color.red())
        await ctx.send(embed=embed)    

bot.run(TOKEN)


