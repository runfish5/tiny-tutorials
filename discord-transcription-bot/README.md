# Creating a Discord Bot Account
1. Log in to the [Discord website](https://discord.com/).
2. Go to the [application page](https://discord.com/developers/applications).
3. Click “New Application,” name it, and click “Create.”
4. Navigate to the “Bot” tab.
5. Check “Public Bot” if you want others to invite it; leave “Require OAuth2 Code Grant” unchecked unless needed.
6. Since your Bot is new, freely click on the "Reset Token" and enter your password. 
7. Copy the token and keep it private, regenerate if leaked.


8. Go to “OAuth2 > URL Generator.”
9. Check “bot” under “OAuth2 URL Generator” and a new box named "Bot permissions" will appear.

10. Under “Bot Permissions”, select "Connect", main permission is recording voices allowance.
11. In the field below a URL specific to the permissions will be generated. Copy and paste it into your browser, choose a server, and click “Authorize” (requires “Manage Server” permission).
E.g. `https://discord.com/oauth2/authorize?client_id=0808080801234567890permissions=1048576&integration_type=0&scope=bot`

Great! So now when we start up the bot somewhere and assign it the secret token, then it will have the rights to record users speeches.



# Turn on the bot

1. Open the notebook in google colab
2. `ctrl + H` and search `DISCORD_BOT_TOKEN`. Insert your bot-token at `env_content = """DISCORD_BOT_TOKEN=` or run all cells until that cell and insert the token directly in the .env file for additional token leakage protection.
3. For the whisperx align model, we additionally need the HuggingFace token, which you can create here: https://huggingface.co/settings/tokens.
4. In google colab in the leftside menu bar is a icon of a key. Click on it and select `Add new secret. Name it `HF_TOKEN` and paste your new Huggingface token in there. Toggle the `Notebook access` so it shows a tick.
5. Now you're all set! Run all cells above and including the cell `Execute main.py`. This cells output should now be `Bot is RUNNING. 🔴 `. Now you can use the bot in discord.

# Use the bot in Discord

1. We defined the function to start the Bot in `main.py`, hence you can now add it to the channel by sending `/record` in any chat of voice channels.

      If it doesn't work, check permissions:
      * Open the voice channel settings → `Edit Channel` → `Permissions`, and ensure the bot has access.
      * If the bot isn’t listed, add it directly as a **member**. (Granting permissions to a **role** may not be effective.)


3. When you like to transcribe the conversation, send `stop_recording`, and a new folder will appear (`/content/tiny-tutorials/discord-transcription-bot/recordings/`).
4. You can transcribe all recordings by running all cells in chapter `Step 3`.
