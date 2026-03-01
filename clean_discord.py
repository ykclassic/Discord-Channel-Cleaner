import discord
import asyncio
from datetime import datetime, timedelta, timezone
import os
import time

# Configuration from Environment Variables
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNELS_RAW = os.getenv('CHANNEL_ID')
LOG_CHANNEL_ID_STR = os.getenv('LOG_CHANNEL_ID')

# Safety Constraints to prevent 4-hour runs
MAX_MESSAGES_PER_CHANNEL = 2000 
SCRIPT_TIMEOUT_SECONDS = 900 # 15-minute emergency shutoff

class CleanerClient(discord.Client):
    async def on_ready(self):
        start_time = time.time()
        print(f"--- Optimized Multi-Channel Cleanup ---")
        
        if not CHANNELS_RAW:
            print("ERROR: No CHANNEL_ID found in secrets.")
            await self.close()
            return

        # Handles "ID1,ID2" or "ID1, ID2" automatically
        channel_ids = [id.strip() for id in CHANNELS_RAW.split(',') if id.strip()]
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        reports = []

        for cid in channel_ids:
            # Check if we are approaching the 15-minute timeout
            if time.time() - start_time > SCRIPT_TIMEOUT_SECONDS:
                print("⚠️ Script timeout reached. Ending session to save minutes.")
                break

            try:
                channel = self.get_channel(int(cid))
                if not channel:
                    print(f"⚠️ Could not find channel {cid}")
                    continue

                print(f"Cleaning #{channel.name}...")
                total_deleted = 0
                
                while total_deleted < MAX_MESSAGES_PER_CHANNEL:
                    if time.time() - start_time > SCRIPT_TIMEOUT_SECONDS: break
                    
                    batch_size = min(100, MAX_MESSAGES_PER_CHANNEL - total_deleted)
                    # purge() handles the 14-day rule logic automatically
                    deleted = await channel.purge(before=cutoff, limit=batch_size, oldest_first=True)
                    total_deleted += len(deleted)
                    
                    if len(deleted) == 0: break
                    await asyncio.sleep(1) # Respect Rate Limits

                reports.append(f"• <#{cid}>: {total_deleted} messages")

            except Exception as e:
                print(f"❌ Error on {cid}: {e}")

        # Summary Log
        if reports and LOG_CHANNEL_ID_STR:
            log_channel = self.get_channel(int(LOG_CHANNEL_ID_STR))
            if log_channel:
                report_text = f"🗓️ **Cleanup Report**\n" + "\n".join(reports)
                await log_channel.send(report_text)

        await self.close()

async def main():
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True
    client = CleanerClient(intents=intents)
    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
