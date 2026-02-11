import discord
from discord.ext import commands
import requests       
import yt_dlp
import os
import asyncio

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
class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # {guild_id: [songs]}

    def ensure_voice(self, ctx):
        if not ctx.author.voice:
            raise commands.CommandError("¡Debes estar en un canal de voz!")
        return ctx.author.voice.channel

    async def ensure_voice_client(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_connected():
            return ctx.voice_client
        voice_channel = self.ensure_voice(ctx)
        vc = await voice_channel.connect()
        return vc

    async def get_song_url(self, search):
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = await loop.run_in_executor(ydl.extract_info, f"ytsearch:{search}", download=False)
            return info["entries"][0]["url"]

    async def play_next(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.queues or not self.queues[guild_id]:
            return

        url = self.queues[guild_id].pop(0)
        vc = ctx.voice_client
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        vc.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))

    @commands.command(name="play")
    async def play(self, ctx, *, search):
        vc = await self.ensure_voice_client(ctx)
        
        if vc.is_playing() or vc.is_paused():
            guild_id = ctx.guild.id
            if guild_id not in self.queues:
                self.queues[guild_id] = []
            
            url = await self.get_song_url(search)
            self.queues[guild_id].append(url)
            return await ctx.send(f"**Agregado a la cola** 🎵 (Posición: {len(self.queues[guild_id])})")

        url = await self.get_song_url(search)
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        vc.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
        await ctx.send(f"**Reproduciendo ahora** ▶️ `{search}`")

    @commands.command(name="skip")
    async def skip(self, ctx):
        vc = ctx.voice_client
        if not vc or not vc.is_playing():
            return await ctx.send("❌ Nada reproduciendo.")

        vc.stop()
        await ctx.send("⏭ **Saltada**")

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.queues or not self.queues[guild_id]:
            return await ctx.send("📭 **Cola vacía**")

        embed = discord.Embed(title="📋 Cola de reproducción", color=0x00ff00)
        for i, _ in enumerate(self.queues[guild_id]):
            embed.add_field(name=f"{i+1}. Canción", value="Cargando...", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="clear")
    async def clear(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.queues:
            self.queues[guild_id].clear()
        await ctx.send("🗑 **Cola limpiada**")

    @commands.command(name="leave", aliases=["stop"])
    async def leave(self, ctx):
        vc = ctx.voice_client
        if vc:
            guild_id = ctx.guild.id
            if guild_id in self.queues:
                self.queues[guild_id].clear()
            await vc.disconnect()
            await ctx.send("👋 **Desconectado**")

async def setup(bot):
    await bot.add_cog(MusicCog(bot))

    


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




