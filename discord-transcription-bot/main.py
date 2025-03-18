import discord
import tempfile
import os
import threading
import asyncio
from model_config import model  # Import the model from our config file

bot = discord.Bot()
connections = {}
should_exit = False

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

def input_listener():
    """Listen for keyboard input to gracefully stop the bot"""
    global should_exit
    while not should_exit:
        user_input = input("Press Enter to stop the bot gracefully...\n")
        if user_input == "" or user_input:  # Any input will work
            print("Stopping bot gracefully...")
            should_exit = True
            # Schedule the bot to close in the bot's event loop
            asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
            break

if __name__ == "__main__":
    if model is None:
        print("Error: Whisper model not loaded. Please run from the notebook.")
    else:
        # Start input listener in a separate thread
        input_thread = threading.Thread(target=input_listener, daemon=True)
        input_thread.start()
        
        print("Bot is starting. Press Enter at any time to stop gracefully.")
        try:
            bot.run(os.getenv("DISCORD_BOT_TOKEN"))
        except Exception as e:
            print(f"Bot stopped with error: {e}")
        finally:
            should_exit = True
            print("Bot has been stopped.")
