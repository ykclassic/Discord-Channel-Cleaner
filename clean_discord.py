import discord
import asyncio
from datetime import datetime, timedelta, timezone
import os
import sys

# Configuration from Environment Variables
TOKEN = os.getenv('DISCORD_TOKEN')
# Using a string first to handle potential formatting issues
CHANNEL_ID_STR = os.getenv('CHANNEL_ID')

class CleanerClient(discord.Client):
    async def on_ready(self):
        print(f"--- Connection Successful ---")
        print(f"Logged in as: {self.user} (ID: {self.user.id})")
        
        # --- DEBUG BLOCK: Visualizing Bot Access ---
        print(f"Connected to {len(self.guilds)} server(s):")
        for guild in self.guilds:
            print(f" - {guild.name} (ID: {guild.id})")
        
        if not CHANNEL_ID_STR:
            print("ERROR: CHANNEL_ID environment variable is missing in GitHub Secrets.")
            await self.close()
            return

        try:
            # Clean the ID string in case of accidental spaces/quotes
            target_id = int(''.join(filter(str.isdigit, CHANNEL_ID_STR)))
            channel = self.get_channel(target_id)
            
            if channel is None:
                print(f"ERROR: Could not find channel with ID {target_id}.")
                print("POSSIBLE REASONS:")
                print("1. The Bot is not invited to the server listed above.")
                print("2. The Bot does not have 'View Channel' permissions for that specific channel.")
                print("3. The ID belongs to a Category or Thread, not a Text Channel.")
                await self.close()
                return

            # Calculate the cutoff (24 hours ago)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            
            print(f"Target Channel: #{channel.name} (Server: {channel.guild.name})")
            print(f"Purging messages older than: {cutoff}")

            # Discord's purge logic
            deleted = await channel.purge(before=cutoff, oldest_first=True)
            
            print(f"SUCCESS: Deleted {len(deleted)} messages.")

        except ValueError:
            print(f"ERROR: CHANNEL_ID '{CHANNEL_ID_STR}' is not a valid number.")
        except discord.Forbidden:
            print("ERROR: Bot lacks 'Manage Messages' or 'Read Message History' permissions in that channel.")
        except Exception as e:
            print(f"CRITICAL ERROR: {type(e).__name__}: {e}")
        
        await self.close()

async def main():
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN is missing in GitHub Secrets.")
        sys.exit(1)

    # Required Intents for reading and deleting messages
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True  # Must be enabled in Discord Dev Portal
    
    client = CleanerClient(intents=intents)
    
    try:
        await client.start(TOKEN)
    except discord.LoginFailure:
        print("ERROR: Invalid DISCORD_TOKEN. Please check your GitHub Secrets.")
    except Exception as e:
        print(f"FAILED TO START: {e}")

if __name__ == "__main__":
    asyncio.run(main())
