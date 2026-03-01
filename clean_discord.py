import discord
import asyncio
from datetime import datetime, timedelta, timezone
import os

# Configuration from Environment Variables
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
HOURS_THRESHOLD = 24

class CleanerClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')
        channel = self.get_channel(CHANNEL_ID)
        
        if channel:
            # Calculate the cutoff time (24 hours ago)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_THRESHOLD)
            
            print(f"Purging messages older than {cutoff}...")
            # channel.purge handles the logic for batch deleting
            deleted = await channel.purge(before=cutoff, oldest_first=True)
            print(f"Successfully deleted {len(deleted)} messages.")
        else:
            print("Channel not found. Check your CHANNEL_ID.")
        
        await self.close()

async def main():
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True
    
    client = CleanerClient(intents=intents)
    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
