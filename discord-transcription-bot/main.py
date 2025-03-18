# main.py (modified for notebook environment)
import discord
import tempfile
import os
import threading
import asyncio
import signal
from model_config import model  # Import the model from our config file

class DiscordBot:
    def __init__(self, model):
        self.bot = discord.Bot()
        self.connections = {}
        self.model = model
        self.running = False
        self.bot_task = None
        self.setup_commands()
    
    def setup_commands(self):
        @self.bot.command()
        async def record(ctx):
            voice = ctx.author.voice
            
            if not voice:
                await ctx.respond("⚠️ You aren't in a voice channel!")
                return
                
            vc = await voice.channel.connect()
            self.connections.update({ctx.guild.id: vc})
            
            vc.start_recording(
                discord.sinks.WaveSink(),
                lambda sink, channel, *args: self.once_done(sink, channel, *args),
                ctx.channel,
            )
            await ctx.respond("🔴 Listening to this conversation.")
        
        @self.bot.command()
        async def stop_recording(ctx):
            if ctx.guild.id in self.connections:
                vc = self.connections[ctx.guild.id]
                vc.stop_recording()
                del self.connections[ctx.guild.id]
                await ctx.delete()
            else:
                await ctx.respond("🚫 Not recording here")
    
    async def once_done(self, sink, channel, *args):
        recorded_users = [f"<@{user_id}>" for user_id in sink.audio_data.keys()]
        await sink.vc.disconnect()
        
        transcript = ""
        
        for user_id, audio in sink.audio_data.items():
            audio_buffer = audio.file.read()
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio:
                temp_audio.write(audio_buffer)
                temp_audio.flush()
                
                result = self.model.transcribe(temp_audio.name)
                
            user_transcript = f"\n\nSpeaker {user_id}: {result['text']}"
            transcript += user_transcript
        
        await channel.send(f"<transcript>:\n\n{transcript}\n\n</transcript>")
    
    async def _start_bot(self):
        """Start the bot in the background"""
        await self.bot.start(os.getenv("DISCORD_BOT_TOKEN"))
        
    def start(self):
        """Non-blocking method to start the bot"""
        if self.running:
            print("Bot is already running")
            return
            
        print("Starting Discord bot... Press Enter in any cell to stop.")
        self.running = True
        loop = asyncio.get_event_loop()
        self.bot_task = loop.create_task(self._start_bot())
    
    async def stop(self):
        """Stop the bot gracefully"""
        if not self.running:
            print("Bot is not running")
            return
            
        print("Stopping Discord bot...")
        self.running = False
        await self.bot.close()
        if self.bot_task:
            if not self.bot_task.done():
                self.bot_task.cancel()
            self.bot_task = None
        print("Discord bot stopped successfully")
