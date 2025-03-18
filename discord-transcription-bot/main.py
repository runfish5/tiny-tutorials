import discord
import tempfile
import whisper
from dotenv import load_dotenv
from os import environ as env

bot = discord.Bot()
connections = {}
load_dotenv()

model = whisper.load_model("base")

@bot.command()
async def record(ctx):
    voice = ctx.author.voice
    
    if not voice:
        await ctx.respond("⚠️ You aren't in a voice channel!")
        return
        
    vc = await voice.channel.connect()
    connections.update({ctx.guild.id: vc})
    
    vc.start_recording(
        discord.sinks.WaveSink(),
        once_done,
        ctx.channel,
    )
    await ctx.respond("🔴 Listening to this conversation.")

async def once_done(sink, channel, *args):
    recorded_users = [f"<@{user_id}>" for user_id in sink.audio_data.keys()]
    await sink.vc.disconnect()
    
    transcript = ""
    
    for user_id, audio in sink.audio_data.items():
        audio_buffer = audio.file.read()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio:
            temp_audio.write(audio_buffer)
            temp_audio.flush()
            
            result = model.transcribe(temp_audio.name)
            
        user_transcript = f"\n\nSpeaker {user_id}: {result['text']}"
        transcript += user_transcript
    
    await channel.send(f"<transcript>:\n\n{transcript}\n\n</transcript>")

@bot.command()
async def stop_recording(ctx):
    if ctx.guild.id in connections:
        vc = connections[ctx.guild.id]
        vc.stop_recording()
        del connections[ctx.guild.id]
        await ctx.delete()
    else:
        await ctx.respond("🚫 Not recording here")

bot.run(env.get("DISCORD_BOT_TOKEN"))
