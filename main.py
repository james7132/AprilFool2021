import discord
import os
import collections
from discord.ext import commands

# Keyed by voice channel ID, value is
MAPPINGS = {
    163175631562080257: 170094554509344770
}

intents = discord.Intents.none()
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(
    max_messages=None,
    member_cache_flags=discord.MemberCacheFlags.voice,
    intents=intents)

@bot.listener()
async def on_ready():
    print("Bot ready!")
    print(f"Logged in as {bot.user}!")

@bot.listener()
async def on_voice_state_update(member, before, after):
    if before.channel == after.channel:
        return
    try:
        if before.channel is not None:
            channel_id = MAPPINGS.get(before.channel.id)
            channel = member.guild.get_channel(channel_id)
            if channel is not None and member in channel.overwrites:
                await before.channel.set_permissions(member, overwrite=None)
                print(f"Removed access to {channel.id} from {member.id}")
    except:
        pass

    try:
        if after.channel is not None:
            channel_id = MAPPINGS.get(before.channel.id)
            channel = member.guild.get_channel(channel_id)
            if channel is not None:
                perms = discord.PermissionOverwrite(read_messages=True)
                await after.channel.set_permissions(member, overwrite=perms)
                print(f"Granted access to {channel.id} from {member.id}")
    except:
        pass

if __main__:
    bot.run(token=os.env["DISCORD_TOKEN"])
