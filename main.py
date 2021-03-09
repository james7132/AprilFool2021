import discord
import os
import collections

# Keyed by voice channel ID, value is
MAPPINGS = {
    163175631562080257: 170094554509344770,
    749336537879150752: 818750722703097866
}

intents = discord.Intents.none()
intents.guilds = True
intents.voice_states = True

cache_flags = discord.MemberCacheFlags.none()
cache_flags.voice = True

bot = discord.Client(
    max_messages=None,
    member_cache_flags=cache_flags,
    intents=intents)

@bot.event
async def on_ready():
    print("Bot ready!")
    print(f"Logged in as {bot.user}!")

def ch(c):
    return c.id if c is not None else 0

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel == after.channel:
        return
    before_id = MAPPINGS.get(ch(before.channel))
    after_id = MAPPINGS.get(ch(after.channel))
    before_channel = member.guild.get_channel(before_id)
    after_channel = member.guild.get_channel(after_id)
    if before_channel == after_channel:
        return

    try:
        if before_channel is not None:
            print(f"{member} left {before.channel}")
            await before_channel.set_permissions(member, overwrite=None)
            print(f"Removed access to {before_channel} from {member}")
    except Exception as e:
        print(e)

    try:
        if after_channel is not None:
            print(f"{member} joined {after.channel}")
            perms = discord.PermissionOverwrite(read_messages=True)
            await after_channel.set_permissions(member, overwrite=perms)
            print(f"Granted access to {after_channel} for {member}")
    except Exception as e:
        print(e)

bot.run(os.environ["DISCORD_TOKEN"])
