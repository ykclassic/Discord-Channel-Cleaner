import discord
import asyncio
from datetime import datetime, timedelta, timezone
import os
import time

# Configuration from Environment Variables
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNELS_RAW = os.getenv('CHANNEL_ID')
LOG_CHANNEL_ID_STR = os.getenv('LOG_CHANNEL_ID')

# Revised Constraints for Speed
MAX_MESSAGES_PER_CHANNEL = 200 # Now set to 200 as requested
SCRIPT_TIMEOUT_SECONDS = 900    # 15-minute hard stop to save GitHub minutes

class CleanerClient(discord.Client):
    async def on_ready(self):
        start_time = time.time()
        print(f"--- Fast Multi-Channel Cleanup Started ---")
        
        if not CHANNELS_RAW:
            print("ERROR: No CHANNEL_ID found in GitHub Secrets.")
            await self.close()
            return

        # Handles "ID1,ID2" or "ID1, ID2" by stripping whitespace
        channel_ids = [id.strip() for id in CHANNELS_RAW.split(',') if id.strip()]
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        reports = []

        for cid in channel_ids:
            # Emergency exit if the total script time exceeds 15 minutes
            if time.time() - start_time > SCRIPT_TIMEOUT_SECONDS:
                print("⚠️ Global timeout reached. Stopping.")
                break

            try:
                target_id = int(cid)
                channel = self.get_channel(target_id)
                
                if not channel:
                    print(f"⚠️ Could not find channel ID: {target_id}")
                    continue

                print(f"Cleaning #{channel.name} (Max 200)...")
                
                # Delete exactly up to 200 messages older than 24h
                deleted = await channel.purge(
                    before=cutoff, 
                    limit=MAX_MESSAGES_PER_CHANNEL, 
                    oldest_first=True
                )
                
                count = len(deleted)
                reports.append(f"• <#{target_id}>: {count} messages")
                print(f"Done. Deleted {count} messages.")

                # Short pause between channels to stay under the radar
                await asyncio.sleep(2)

            except Exception as e:
                print(f"❌ Error on channel {cid}: {e}")

        # Send the Final Report
        if reports and LOG_CHANNEL_ID_STR:
            try:
                log_channel = self.get_channel(int(LOG_CHANNEL_ID_STR))
                if log_channel:
                    summary = f"🗓️ **Cleanup Report**\n" + "\n".join(reports)
                    await log_channel.send(summary)
            except:
                print("Could not send log message.")

        await self.close()

async def main():
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True 
    client = CleanerClient(intents=intents)
    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
