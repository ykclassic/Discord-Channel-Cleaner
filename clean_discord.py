import discord
import asyncio
from datetime import datetime, timedelta, timezone
import os
import sys

# Configuration from Environment Variables
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID_STR = os.getenv('CHANNEL_ID')
LOG_CHANNEL_ID_STR = os.getenv('LOG_CHANNEL_ID') # Optional: Add a separate ID for logs

class CleanerClient(discord.Client):
    async def on_ready(self):
        print(f"--- Connection Successful ---")
        
        if not CHANNEL_ID_STR:
            print("ERROR: CHANNEL_ID missing.")
            await self.close()
            return

        try:
            target_id = int(''.join(filter(str.isdigit, CHANNEL_ID_STR)))
            channel = self.get_channel(target_id)
            
            if channel is None:
                print(f"ERROR: Could not find channel {target_id}")
                await self.close()
                return

            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            print(f"Purging #{channel.name} messages older than: {cutoff}")

            # Unlimited Purge: Loop until all old messages are gone
            total_deleted = 0
            while True:
                # Use a high limit to clear large spans of spam
                deleted = await channel.purge(before=cutoff, limit=500, oldest_first=True)
                total_deleted += len(deleted)
                if len(deleted) < 500: # If we deleted fewer than the limit, we're done
                    break
            
            summary_msg = f"✅ **Cleanup Report**: Cleared **{total_deleted}** messages from <#{target_id}> (Older than 24hrs)."
            print(summary_msg)

            # Logging Feature: Send report to a channel
            log_id = int(LOG_CHANNEL_ID_STR) if LOG_CHANNEL_ID_STR else target_id
            log_channel = self.get_channel(log_id)
            if log_channel:
                await log_channel.send(summary_msg)

        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
        
        await self.close()

async def main():
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True
    client = CleanerClient(intents=intents)
    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
