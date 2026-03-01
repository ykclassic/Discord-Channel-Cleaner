import discord
import asyncio
from datetime import datetime, timedelta, timezone
import os
import sys

# Configuration from Environment Variables
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNELS_RAW = os.getenv('CHANNEL_ID') # Now expects "ID1, ID2, ID3"
LOG_CHANNEL_ID_STR = os.getenv('LOG_CHANNEL_ID')

class CleanerClient(discord.Client):
    async def on_ready(self):
        print(f"--- Multi-Channel Cleanup Started ---")
        print(f"Logged in as: {self.user}")

        if not CHANNELS_RAW:
            print("ERROR: No CHANNEL_ID provided.")
            await self.close()
            return

        # Split comma-separated IDs and clean whitespace
        channel_ids = [id.strip() for id in CHANNELS_RAW.split(',') if id.strip()]
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        reports = []

        for cid in channel_ids:
            try:
                target_id = int(cid)
                channel = self.get_channel(target_id)
                
                if channel is None:
                    print(f"⚠️ Could not find or access channel ID: {target_id}")
                    continue

                print(f"Processing #{channel.name} in {channel.guild.name}...")
                
                total_deleted = 0
                while True:
                    # Purge in batches of 500
                    deleted = await channel.purge(before=cutoff, limit=500, oldest_first=True)
                    total_deleted += len(deleted)
                    if len(deleted) < 500:
                        break
                
                reports.append(f"• <#{target_id}>: {total_deleted} messages")
                print(f"Done. Deleted {total_deleted} messages.")

            except Exception as e:
                print(f"❌ Error on channel {cid}: {e}")

        # Send Final Summary Log
        if reports:
            summary_body = "\n".join(reports)
            summary_header = f"🗓️ **Cleanup Report ({datetime.now().strftime('%Y-%m-%d %H:%M')})**\n"
            full_report = f"{summary_header}{summary_body}\n*Criteria: Older than 24hrs*"

            log_id = int(LOG_CHANNEL_ID_STR) if LOG_CHANNEL_ID_STR else None
            if log_id:
                log_channel = self.get_channel(log_id)
                if log_channel:
                    await log_channel.send(full_report)
            else:
                print("No LOG_CHANNEL_ID set. Summary printed to console.")

        await self.close()

async def main():
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True
    client = CleanerClient(intents=intents)
    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
