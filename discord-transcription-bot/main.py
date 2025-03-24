get_bot_status()



# model_config.model = model
print("Model assigned to configuration")

# Execute main.py
exec(open("main.py").read())

# Global stop flag
running = True

async def keep_alive():
    global running
    while running:
        await asyncio.sleep(1)  # Keep the loop alive without blocking

# Start the bot and the keep-alive task
loop = asyncio.get_event_loop()
bot_task = loop.create_task(run_bot())
keep_alive_task = loop.create_task(keep_alive())

get_bot_status()
