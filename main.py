from discord.ext import commands
from discord_components import *
import discord, os, sqlite3

intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True)
client = commands.Bot(command_prefix='=', intents=intents)
client.remove_command('help')

with sqlite3.connect('main.db', timeout=60) as db:
    cur = db.cursor()
    cur.execute(f'''CREATE TABLE IF NOT EXISTS users (guild_id int, user_id int, user_name text, elo int, wins int, loss int)''')
    cur.execute(f'''CREATE TABLE IF NOT EXISTS bans (guild_id int, user_id int, length int, reason text, banned_by text)''')
    cur.execute(f'''CREATE TABLE IF NOT EXISTS maps (guild_id int, map_list text)''')
    cur.execute(f'''CREATE TABLE IF NOT EXISTS settings (guild_id int, reg_role int, map_pick_phase text, team_cap_vcs text, picking_phase text, queue_channel int, reg_channel int, win_elo int, loss_elo int, match_logs int)''')
    cur.execute(f'''CREATE TABLE IF NOT EXISTS matches (guild_id int, match_id int, map text, orange_cap text, orange_team text, blue_cap text, blue_team text, status text, winners text)''')
    db.commit()

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        return
    raise error
    
@client.event
async def on_member_remove(member):
    with sqlite3.connect('main.db', timeout=60) as db:
        cur = db.cursor()
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {member.guild.id} AND user_id = {member.id});").fetchall()[0] == (1,):
            cur.execute(f"DELETE FROM users WHERE guild_id = {member.guild.id} AND user_id = {member.id};")
            db.commit()

@client.event
async def on_ready():
    DiscordComponents(client)
    print(f'Launched: {client.user.name} // {client.user.id}')
    await client.change_presence(activity=discord.Game(name="Ten Man's | =help"))

for filename in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cogs')):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')
        print(f'Loaded: cog.{filename[:-3]}')


client.run('ODgzMDA2NjA5MjgwODY0MjU3.YTDp_Q.TE1n942meMxyEUc2DLEgB9xY_gM')