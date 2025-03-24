import discord
import os
import time
import asyncio
import json

bot = discord.Bot()
connections = {}

# Ensure the "recordings" directory exists
if not os.path.exists("recordings"):
    os.makedirs("recordings")

# Custom sink to track session and user recording start times
class TimedWaveSink(discord.sinks.WaveSink):
    def __init__(self, session_start_time):
        super().__init__()
        self.session_start_time = session_start_time  # Time when the recording session started
        self.start_times = {}  # Dictionary to store user_id -> start_time

    def write(self, data, user):
        # Record the time when the first audio packet is received for a user
        if user not in self.start_times:
            self.start_times[user] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        super().write(data, user)

@bot.command()
async def record(ctx):
    voice = ctx.author.voice
    
    if not voice:
        await ctx.respond("⚠️ You aren't in a voice channel!")
        return
        
    vc = await voice.channel.connect()
    connections.update({ctx.guild.id: vc})
    
    # Capture the session start time
    session_start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    sink = TimedWaveSink(session_start_time)
    
    # Start recording with the custom sink
    vc.start_recording(
        sink,
        once_done,
        ctx.channel,
    )
    await ctx.respond("🔴 Listening to this conversation.")

async def once_done(sink, channel, *args):
    # Generate session ID and stop time
    session_id = time.strftime("%Y%m%d_%HM%S", time.gmtime())
    session_stop_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    voice_channel = sink.vc.channel.name if sink.vc.channel else "Unknown"
    
    # Process each user's audio
    for user_id, audio in sink.audio_data.items():
        # Create user-specific directory
        user_dir = f"recordings/{user_id}"
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        
        # Save audio file
        audio_file = f"session_{session_id}.wav"
        audio_path = os.path.join(user_dir, audio_file)
        with open(audio_path, "wb") as f:
            f.write(audio.file.read())
        
        # Gather user metadata
        member = channel.guild.get_member(user_id)
        username = member.name if member else "Unknown"
        discriminator = member.discriminator if member else "0000"
        
        # Get the user's recording start time
        recording_start_time = sink.start_times[user_id]
        
        # Define the recording entry with timing information
        recording_entry = {
            "session_id": session_id,
            "session_start_time": sink.session_start_time,  # When the recording command was issued
            "user_recording_start_time": recording_start_time,  # When this user first spoke
            "session_stop_time": session_stop_time,  # When recording stopped
            "voice_channel": voice_channel,
            "audio_file": audio_file,
            "username": username,
            "discriminator": discriminator
        }
        
        # Update metadata.json
        metadata_path = os.path.join(user_dir, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        else:
            metadata = {"recordings": []}
            # Optionally, add initial_voice_engagement for the user's first-ever recording
            # recording_entry["initial_voice_engagement"] = recording_start_time
        
        metadata["recordings"].append(recording_entry)
        
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=4)
    
    # Disconnect and notify
    await sink.vc.disconnect()
    await channel.send(f"Recording stopped. Audio files saved for session {session_id}.")

@bot.command()
async def stop_recording(ctx):
    if ctx.guild.id in connections:
        vc = connections[ctx.guild.id]
        vc.stop_recording()
        del connections[ctx.guild.id]
        await ctx.respond("🛑 Recording stopped.")
    else:
        await ctx.respond("🚫 Not recording here")

async def run_bot():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("Error: DISCORD_BOT_TOKEN environment variable not set.")
        return
    await bot.start(token)

if __name__ == "__main__":
    print("This script is meant to be run from the notebook.")
