import discord
from discord.ext import commands
import requests       
import yt_dlp
import os


from dotenv import load_dotenv
load_dotenv()


intents = discord.Intents.default()    
intents.message_content = True

bot = commands.Bot(command_prefix='$',intents=intents)





YDL_OPTIONS = {
    "format": "bestaudio",
    "quiet": True
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}


@bot.event
async def on_ready():
    print(f"Estoy funcionando {bot.user}")

#--------------------VOZ-------------------
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
    else:
        await ctx.send("Conéctate a un canal de voz 😪")

@bot.command()
async def leave (ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

#--------------------Música--------------------
@bot.command()
async def play(ctx, *, search):
    if not ctx.author.voice:
        return await ctx.send("Debes estar en un canal de voz 😪")
    
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()
    
    vc = ctx.voice_client

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{search}", download=False)
        url = info["entries"][0]["url"]
    
    if vc.is_playing():
        vc.stop()
    
    vc.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
    await ctx.send (f"reproduciendo 🎶: **{search}**")

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()


@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()

    
#--------------------POKEMON---------------

@bot.command()
async def poke(ctx, arg):
    try:
        pokemon =  arg.split(" ",1)[0].lower()
        result = requests.get("https://pokeapi.co/api/v2/pokemon/"+pokemon)
        if result.text == "Not Found":
           await ctx.send ("Pokemon no encontrado 😭")
        else:
            image_url = result.json()['sprites']['front_default']
            print(image_url)
            await ctx.send (image_url)
    except Exception as e:
        print("Error: ", e)


@poke.error
async def error_type(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send("Tienes que pasarme un Pokemon 🫠")


#--------------------LIMPIEZA--------------------
@bot.command()
async def limpiar(ctx):
    await ctx.channel.purge()
    await ctx.send ("Mensajes eliminados 🧹", delete_after=3)


#--------------------Arranque--------------------
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)



