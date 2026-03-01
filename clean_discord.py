import discord
import asyncio
from datetime import datetime, timedelta, timezone
import os
import sys

# Configuration from Environment Variables
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID_STR = os.getenv('CHANNEL_ID')

class CleanerClient(discord.Client):
    async def on_ready(self):
        print(f'--- Connection Successful ---')
        print(f'Logged in as: {self.user} (ID: {self.user.id})')
        
        if not CHANNEL_ID_STR:
            print("ERROR: CHANNEL_ID environment variable is missing.")
            await self.close()
            return

        try:
            channel_id = int(CHANNEL_ID_STR)
            channel = self.get_channel(channel_id)
            
            if channel is None:
                print(f"ERROR: Could not find channel with ID {channel_id}.")
                print("Check if the Bot is a member of the server where the channel exists.")
                await self.close()
                return

            # Calculate the cutoff time (24 hours ago)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            
            print(f"Purging messages in #{channel.name} older than {cutoff}...")
            deleted = await channel.purge(before=cutoff, oldest_first=True)
            print(f"SUCCESS: Deleted {len(deleted)} messages.")

        except discord.Forbidden:
            print("ERROR: Bot lacks 'Manage Messages' or 'Read History' permissions.")
        except Exception as e:
            print(f"CRITICAL ERROR: {type(e).__name__}: {e}")
        
        await self.close()

async def main():
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN environment variable is missing.")
        sys.exit(1)

    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True  # Ensure this is enabled in Dev Portal
    
    client = CleanerClient(intents=intents)
    try:
        await client.start(TOKEN)
    except discord.LoginFailure:
        print("ERROR: Invalid DISCORD_TOKEN.")

if __name__ == "__main__":
    asyncio.run(main())
