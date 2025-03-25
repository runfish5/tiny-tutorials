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

class TimedWaveSink(discord.sinks.WaveSink):
    def __init__(self, session_start_time):
        super().__init__()
        self.session_start_time = session_start_time  # String, e.g., "2023-10-25 12:00:00"
        self.start_times = {}  # user_id -> start_time (float, seconds since epoch)

    def write(self, data, user):
        # Ensure user is valid and record start time with high precision
        if user is not None and user not in self.start_times:
            self.start_times[user] = time.time()
            print(f"Set start time for user {user}: {self.start_times[user]}")
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
    ctx.respond(f"session_start_time: {str(session_start_time)}")
    sink = TimedWaveSink(session_start_time)
    
    # Start recording with the custom sink
    vc.start_recording(
        sink,
        once_done,
        ctx.channel,
    )
    await ctx.respond("🔴 Listening to this conversation.")

async def once_done(sink, channel, *args):
    session_id = time.strftime("%Y%m%d_%HM%S", time.gmtime())
    session_stop_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    voice_channel = sink.vc.channel.name if sink.vc.channel else "Unknown"
    
    for user_id, audio in sink.audio_data.items():
        member = channel.guild.get_member(user_id)
        username = member.name if member else "Unknown"
        discriminator = member.discriminator if member else "0000"
        
        user_dir = f"recordings/{username}"
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        
        audio_file = f"session_{session_id}.wav"
        audio_path = os.path.join(user_dir, audio_file)
        with open(audio_path, "wb") as f:
            f.write(audio.file.read())
        
        # Get start time, falling back to session_start_time if missing (rare)
        recording_start_time = sink.start_times.get(user_id)
        if recording_start_time is None:
            # Log this for debugging; should not happen
            print(f"Warning: No start time for user {user_id}, using session start")
            recording_start_time = time.mktime(time.strptime(sink.session_start_time, "%Y-%m-%d %H:%M:%S"))
        
        # Convert float timestamp to string with microsecond precision
        # start_time_str = time.strftime("%Y-%m-%d %H:%M:%S.%f", time.gmtime(recording_start_time))
        start_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(recording_start_time))
        recording_entry = {
            "session_id": session_id,
            "session_start_time": sink.session_start_time,
            "user_recording_start_time": start_time_str,
            "session_stop_time": session_stop_time,
            "voice_channel": voice_channel,
            "audio_file": audio_file,
            "username": username,
            "discriminator": discriminator
        }
        
        metadata_path = os.path.join(user_dir, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        else:
            metadata = {"recordings": []}
        
        metadata["recordings"].append(recording_entry)
        
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=4)
    
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
