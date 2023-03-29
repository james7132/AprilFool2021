import asyncio
import json
import random
import discord
import os
import csv
import collections
from discord.ext import commands

IMPORT_DATA = "roles.csv"
OUTPUT_DATA = "data.json"
BASE_COST = 100000
COST_GROWTH = 2.50
PAYOUT_MIN = 50000
PAYOUT_MAX = 75000

bot = commands.Bot(
    max_messages=None,
    command_prefix='!',
    member_cache_flags=discord.MemberCacheFlags.all(),
    intents=discord.Intents.all())

with open(OUTPUT_DATA, "r+") as f:
    data = json.load(f)

def save_data(data):
    with open(OUTPUT_DATA, "w") as f:
        json.dump(data, f)

@bot.event
async def on_ready():
    print("Bot ready!")
    print(f"Logged in as {bot.user}!")

async def get_confirmation(bot, check):
    decided = None
    while decided is None:
        msg = await bot.wait_for('message', check=check, timeout=30)
        decided = {
            'y': True,
            'yes': True,
            'n': False,
            'no': False,
        }.get(msg.content.lower())
    return decided

@bot.listen()
async def on_message(message):
    if message.author.bot or message.channel.id == 372835728574382090:
        return
    global BASE_COST, PAYOUT_MIN, PAYOUT_MAX, data
    cnt = message.content
    if any(cnt.startswith(a) for a in ['!', '~', '%', '\'']):
        return
    key = str(message.author.id)
    payout = random.randint(PAYOUT_MIN, PAYOUT_MAX)
    if key in data['users']:
        data['users'][key]['money'] += payout
    else:
        data['users'][key] = {
            'money': payout,
            'next_roll': BASE_COST,
        }
    save_data(data)
    print(f"Gave ${payout} to {message.author}")

# @bot.command(name="import")
# async def import_roles(ctx):
    # """Imports all of the preplanned roles into the server."""
    # global data
    # with open(IMPORT_DATA, 'r') as f:
        # reader = csv.reader(f)
        # for row in reader:
            # print(row)
            # name = row[0]
            # weight = int(row[2])
            # lore = row[5]
            # if row[1]:
                # color = int(row[1][1:], 16)
            # else:
                # color = discord.Colour.default()
            # if 'roles' not in data:
                # data['roles'] = {}
            # if any(r['name'] == name for r in data['roles'].values()):
                # print("Skipping ", name, " already made.")
                # continue
            # role = await ctx.guild.create_role(
                # name=name,
                # color=color,
                # permissions=discord.Permissions.none(),
                # mentionable=False,
                # hoist=False)

            # data['roles'][role.id] = {
                # 'id': role.id,
                # 'name': name,
                # 'weight': weight,
                # 'lore': lore
            # }
            # save_data(data)
            # print("Created role ", name)

@bot.command()
async def gacha(ctx):
    """Pays money to randomly get one of the roles in the bot."""
    global data
    user = data['users'].get(str(ctx.author.id))
    if user is None:
        await ctx.send(f"Sorry {ctx.author.mention}, I can't give credit! "
                       f"Come back when you are a little, mmmmmmm, RICHER! "
                       f" (Wallet: 0, Roll Cost: **${BASE_COST})**")
        return
    elif user['money'] < user['next_roll']:
        await ctx.send(f"Sorry {ctx.author.mention}, I can't give credit! "
                       f"Come back when you are a little, mmmmmmm, RICHER! "
                       f" (Wallet: {user['money']}, Roll Cost: **${user['next_roll']})**")
        return
    user['money'] -= user['next_roll']
    total_weight = sum(r['weight'] for r in data['roles'].values())
    target_weight = random.randint(0, total_weight)
    role = None
    for gacha_role in data['roles'].values():
        target_weight -= gacha_role['weight']
        if target_weight < 0:
            role = ctx.guild.get_role(int(gacha_role['id']))
            break
    if role in ctx.author.roles:
        await ctx.send(f"You rolled {role.mention}, but you already have it!"
                       f"Your next gacha roll will cost "
                       f"**${user['next_roll']}**")
    else:
        next_cost = int(COST_GROWTH * user['next_roll'])
        user['next_roll'] = next_cost
        suffix = f"Your next gacha roll will cost: {next_cost}"
        await ctx.author.add_roles(role)
        await ctx.send(f"You rolled {role.mention}! " + suffix)
    save_data(data)

@bot.command()
async def goomble(ctx, amount: int, multiplier: float):
    """Stake your money on a life or death gamble!

    Examples:
        ~goomble 20000 5.0 => Bets 20,000 for a payout of -100,000 to 100,000
        ~goomble 50000 1.0 => Bets 50,000 for a payout of -50,000 to 50,000

    There is no limit to your multiplier.

    YOU CAN GO INTO DEBT USING THIS. BEWARE.
    ZAWA.  ZAWA.  ZAWA.  ZAWA.  ZAWA.
    """
    global data
    if amount < 0:
        await ctx.send(f"{ctx.author.mention}, cannot bet negative money!")
        return
    user = data['users'].get(str(ctx.author.id))
    if user is None or user['money'] < 0:
        await ctx.send(f"{ctx.author.mention}, you have no money!")
        return
    elif user['money'] < amount:
        await ctx.send(f"{ctx.author.mention}, you don't have ${amount} to bet!")
        return
    elif multiplier < 5:
        await ctx.send(f"{ctx.author.mention}, YOU WEAK WILLED FOOL. GAMBLE MORE!"
                       f"(Minimum Mulitplier 5x)")
        return

    base_range = random.random()
    direction = random.choice([-1.0, 1.0])
    delta = int(amount * direction * base_range * multiplier)
    user['money'] = int(user['money'] + delta)
    save_data(data)
    await ctx.send(f"{ctx.author.mention}, you gambled {amount} and "
                   f"earned {delta}. You now have **${user['money']}**.")

@bot.command()
async def allin(ctx):
    """Stake ALL money on a life or death gamble with a 10,000x multiplier!

    YOU **WILL** GO INTO DEBT USING THIS. BEWARE.
    ZAWA.  ZAWA.  ZAWA.  ZAWA.  ZAWA.
    """
    global data
    user = data['users'].get(str(ctx.author.id))
    if user is None or user['money'] < 0:
        await ctx.send(f"{ctx.author.mention}, you have no money!")
        return
    await goomble(ctx, user['money'], 10000)

@bot.command()
async def shion(ctx):
    """Burn all of your money."""
    global data
    user = data['users'].get(str(ctx.author.id))
    if user is None:
        await ctx.send("Sorry who are you?")
        return
    if user['money'] < 0:
        await ctx.send("Shion doesn't want your debt!")
        return
    user['money'] = 0
    save_data(data)
    await ctx.send("Shion hungrily devours your wallet. You now have $0.")

@bot.command(hidden=True)
async def gachi(ctx):
    await ctx.send("Fuck you. You probably meant !gacha.")

@bot.command(hidden=True)
async def fumo(ctx):
    """Fumo."""
    global data
    user = data['users'].get(str(ctx.author.id))
    if user is None:
        await ctx.send("Sorry who are you?")
        return
    await ctx.send(f"You could buy {user['money'] / 40} fumos with your money.")

@bot.command()
async def wallet(ctx):
    """Shows how much money you have."""
    try:
        key = str(ctx.author.id)
        await ctx.send(f"You have ${data['users'][key]['money']}")
    except:
        await ctx.send(f"You have nothing. You are poor.")

@bot.command()
async def give(ctx, member: discord.Member, offer: discord.Role):
    """Gives one role to another user."""
    if offer not in ctx.author.roles:
        await ctx.send(f"**{ctx.author.mention}** does not have {offer.mention}")
        return
    if str(offer.id) not in data['roles']:
        await ctx.send(f"**{offer}** is not a gacha role.")
        return

    await ctx.send(f"{member.mention}, **{ctx.author}** would like to give you"
                   f"{offer.mention}. Do you accept? (y/yes/n/no)")

    def check(msg):
        return msg.channel == ctx.channel and msg.author == member
    try:
        decision = await get_confirmation(ctx.bot, check)
    except asyncio.TimeoutError:
        await ctx.send(f"{ctx.author.mention}: Exchange cancelled.")
        return

    if decision:
        await asyncio.gather(*[
            ctx.author.remove_roles(offer),
            member.add_roles(offer),
        ])
        await ctx.send(":handshake: Exchange complete!")
    else:
        await ctx.send(":x: Exchange refused!")

@bot.command()
async def charity(ctx, member: discord.Member, amount: int):
    """Gives another user money."""
    if amount < 0:
        await ctx.send(f"{ctx.author.mention}, DEBIT IS NOT CHARITY!")
        return
    global data, BASE_COST
    src = data['users'].get(str(ctx.author.id))
    dst = data['users'].get(str(member.id))

    if src is None or src['money'] < amount:
        await ctx.send(f"{ctx.author.mention}, you don't have **${amount}** to give!")
        return

    await ctx.send(f"{member.mention}, **{ctx.author}** would like to give you"
                   f"${amount}. Do you accept? (y/yes/n/no)")

    def check(msg):
        return msg.channel == ctx.channel and msg.author == member
    try:
        decision = await get_confirmation(ctx.bot, check)
    except asyncio.TimeoutError:
        await ctx.send(f"{ctx.author.mention}: Charity cancelled.")
        return

    src['money'] -= amount
    if dst is not None:
        dst['money'] += amount
    else:
        data['users'][str(member.id)] = {
            'money': amount,
            'next_roll': BASE_COST,
        }
    save_data(data)
    await ctx.send(":handshake: Exchange complete!")

@bot.command()
async def sacrifice(ctx, role: discord.Role):
    """Sacrifices roles to the gods."""
    global data
    if str(role.id) not in data['roles']:
        await ctx.send(f"**{role}** is not a gacha role.")
        return
    await ctx.author.remove_roles(role)
    await ctx.send(f"{ctx.author.mention}:  Kanako ate your {role}.")

@bot.command()
async def lore(ctx, role: discord.Role):
    """Shows the Touhou Discord History behind a role."""
    global data
    role_data = data['roles'].get(str(role.id))
    if role_data is not None:
        await ctx.send(f"{role.name}: {role_data['lore']}")
    else:
        await ctx.send("Lmao what lore?")

@bot.command()
async def trade(ctx, member: discord.Member,
                offer: discord.Role,
                exchange: discord.Role):
    """Trades one role for another with another user."""
    global data
    if offer not in ctx.author.roles:
        await ctx.send(f"**{member}** does not have {offer.mention}")
        return
    if offer not in ctx.author.roles:
        await ctx.send(f"**{member}** does not have {offer.mention}")
        return
    if exchange not in member.roles:
        await ctx.send(f"**{member}** does not have {exchange.mention}")
        return
    if str(offer.id) not in data['roles']:
        await ctx.send(f"**{offer}** is not a gacha role.")
        return
    if str(exchange.id) not in data['roles']:
        await ctx.send(f"**{exchange}** is not a gacha role.")
        return

    await ctx.send(f"{member.mention}, **{ctx.author}** would like to trade"
                   f"{offer.mention} for {exchange.mention}. Do you accept?"
                   f" (y/yes/n/no)")

    def check(msg):
        return msg.channel == ctx.channel and msg.author == member
    try:
        decision = await get_confirmation(ctx.bot, check)
    except asyncio.TimeoutError:
        await ctx.send(f"{ctx.author.mention}: Exchange cancelled.")
        return

    if decision:
        await asyncio.gather(*[
            ctx.author.add_roles(exchange),
            ctx.author.remove_roles(offer),
            member.add_roles(offer),
            member.remove_roles(exchange)
        ])
        await ctx.send(":handshake: Exchange complete!")
    else:
        await ctx.send(":x: Exchange refused!")



bot.run(os.environ["DISCORD_TOKEN"])
