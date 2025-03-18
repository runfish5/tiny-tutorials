# create this as bot_runner.py
import discord
import tempfile
import os
import threading
import asyncio
import time
from model_config import model  # Import the model from our config file

bot = discord.Bot()
connections = {}
bot_running = False
bot_thread = None
stop_event = threading.Event()

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

def run_bot():
    """Run the bot in a separate thread"""
    global bot_running
    bot_running = True
    
    try:
        bot.run(os.getenv("DISCORD_BOT_TOKEN"))
    except Exception as e:
        print(f"Bot error: {e}")
    finally:
        bot_running = False
        print("Bot has stopped.")

def start_bot():
    """Start the bot in a non-blocking way"""
    global bot_thread, bot_running, stop_event
    
    if bot_running or (bot_thread and bot_thread.is_alive()):
        print("Bot is already running!")
        return
    
    stop_event.clear()
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    print("Bot started in background. Use stop_bot() to stop it.")

def stop_bot():
    """Stop the bot gracefully"""
    global bot_running, bot_thread, stop_event
    
    if not bot_running:
        print("Bot is not running!")
        return
    
    print("Stopping bot...")
    stop_event.set()
    
    # Close the bot's event loop from the main thread
    asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
    
    # Wait for the bot to stop
    start_time = time.time()
    while bot_running and time.time() - start_time < 10:  # Wait up to 10 seconds
        time.sleep(0.5)
    
    if bot_running:
        print("Bot did not stop gracefully. You may need to restart the kernel.")
    else:
        print("Bot stopped successfully.")
