import discord, os, sqlite3
from discord.ext import commands

intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True)
client = commands.Bot(command_prefix='=', intents=intents)
client.remove_command('help')

db = sqlite3.connect('main.db')
cur = db.cursor()
cur.execute(f'''CREATE TABLE IF NOT EXISTS users (guild_id int, user_id int, user_name text, elo int, wins int, loss int)''')
cur.execute(f'''CREATE TABLE IF NOT EXISTS bans (guild_id int, user_id int, length int, reason text, banned_by text)''')
db.commit()

@client.event
async def on_ready():
    print(f'Launched: {client.user.name} // {client.user.id}')

@client.command(description="Loads an extention")
async def load(ctx, extention):
    client.load_extension(f'cogs.{extention}')
    await ctx.send(f"**Loaded {extention}**", delete_after=2)

@client.command(description="Unloads an extention")
async def unload(ctx, extention):
    client.unload_extension(f'cogs.{extention}')
    await ctx.send(f"**Unloaded {extention}**", delete_after=2)

@client.command(description="Reloads an extention")
async def reload(ctx, extention):
    client.unload_extension(f'cogs.{extention}')
    client.load_extension(f'cogs.{extention}')
    await ctx.send(f"**Reloaded {extention}**", delete_after=2)

for filename in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cogs')):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')
        print(f'Loaded: cog.{filename[:-3]}')



client.run('ODgzMDA2NjA5MjgwODY0MjU3.YTDp_Q.Ri7kTw9cAurx0XiGSp-p7qBXICk')