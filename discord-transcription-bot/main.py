import discord
import tempfile
import os
from model_config import model  # Import the model from our config file

bot = discord.Bot()
connections = {}

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
        lambda sink, channel, *args: once_done(sink, channel, model, *args),
        ctx.channel,
    )
    await ctx.respond("🔴 Listening to this conversation.")

async def once_done(sink, channel, model, *args):
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

if __name__ == "__main__":
    if model is None:
        print("Error: Whisper model not loaded. Please run from the notebook.")
    else:
        bot.run(os.getenv("DISCORD_BOT_TOKEN"))


# ==
import asyncio
import signal
import sys

# Add these at the top of your main.py
def signal_handler(sig, frame):
    print('Shutting down gracefully...')
    loop = asyncio.get_event_loop()
    loop.stop()
    connections.clear()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Then at the end of your file, modify your run statement:
if __name__ == "__main__":
    if model is None:
        print("Error: Whisper model not loaded. Please run from the notebook.")
    else:
        try:
            bot.run(os.getenv("DISCORD_BOT_TOKEN"))
        except Exception as e:
            print(f"Error occurred: {e}")
            # Clean up any remaining connections
            for vc in connections.values():
                asyncio.run_coroutine_threadsafe(vc.disconnect(), bot.loop)
            connections.clear()
