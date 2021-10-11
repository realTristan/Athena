from discord.ext import commands
from discord_components import *
from datetime import datetime
import discord, os, sqlite3

intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True)
client = commands.Bot(command_prefix='=', intents=intents)
client.remove_command('help')

with sqlite3.connect('main.db', timeout=60) as db:
    cur = db.cursor()
    cur.execute(f'''CREATE TABLE IF NOT EXISTS users (guild_id int, user_id int, user_name text, elo int, wins int, loss int)''')
    cur.execute(f'''CREATE TABLE IF NOT EXISTS bans (guild_id int, user_id int, length int, reason text, banned_by text)''')
    cur.execute(f'''CREATE TABLE IF NOT EXISTS maps (guild_id int, map_list text)''')
    cur.execute(f'''CREATE TABLE IF NOT EXISTS settings (guild_id int, reg_role int, map_pick_phase text, team_cap_vcs text, picking_phase text, queue_channel int, reg_channel int)''')
    cur.execute(f'''CREATE TABLE IF NOT EXISTS matches (guild_id int, match_id int, map text, orange_cap text, orange_team text, blue_cap text, blue_team text, status text, winners text)''')
    db.commit()

@client.event
async def on_member_remove(member):
    with sqlite3.connect('main.db', timeout=60) as db:
        cur = db.cursor()
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {member.guild.id} AND user_id = {member.id});").fetchall()[0] == (1,):
            cur.execute(f"DELETE FROM users WHERE guild_id = {member.guild.id} AND user_id = {member.id};")
            db.commit()

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        return
    raise error

@client.event
async def on_ready():
    DiscordComponents(client)
    print(f'Launched: {client.user.name} // {client.user.id}')
    await client.change_presence(activity=discord.Game(name="=help"))

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


@client.command()
async def help(ctx):
    embed=discord.Embed(title='TenMan Commands', color=65535)
    embed2=discord.Embed(timestamp=datetime.utcnow(), color=65535)
    embed.add_field(name='‏‏‎ ‎\nJoin', value='Join the current queue\n(Usage: =j)')
    embed.add_field(name=' ‎\nLeave', value='Leave the current queue\n(Usage: =l)')
    embed.add_field(name=' ‎\nPick', value='Pick an user to be on your team\n(Usage: =p @user)')
    embed.add_field(name=' ‎\nSelect Map', value='Pick a map to play\n(Usage: =map name)')
    embed.add_field(name=' ‎\nRename', value='Change your Ten Man username\n(Usage: =rename [name])')
    embed.add_field(name=' ‎\nRegister', value='Register yourself to play in the ten mans\n(Usage: =reg [name])')
    embed.add_field(name=' ‎\nShow Queue', value='Show the current queue\n(Usage: =q)')
    embed.add_field(name=' ‎\nShow Maps', value='Show the current map pool\n(Usage: =maps)')
    embed.add_field(name=' ‎\nShow Stats', value='Show your ten man stats\n(Usage: =stats or =stats @user)')
    embed.add_field(name=' ‎\nLeaderboard', value='Show the ten man leaderboard\n(Usage: =lb)')
    embed.add_field(name='‏‏‎ ‎\nShow Last Match', value='Shows the last match played\n(Usage: =lm)')
    embed.add_field(name=' ‎\nMatch Show', value='Shows a match\n(Usage: =match show [match id]')
    embed.add_field(name=' ‎\nBan [Mod+]', value='Bans a player from the queue\n(Usage: =ban [@user] [length] [reason]')
    embed.add_field(name=' ‎\nUnBan [Mod+]', value='Unbans a player from the queue\n(Usage: =unban [@user]')
    embed.add_field(name=' ‎\nWin [Mod+]', value='Give a win to the mentioned users\n(Usage: =win [@users])')
    embed.add_field(name=' ‎\nLose [Mod+]', value='Give a loss to the mentioned users\n(Usage: =lose [@users])')
    embed.add_field(name=' ‎\nAdd Map [Mod+]', value='Adds a map to the map pool\n(Usage: =addmap [name])')
    embed.add_field(name=' ‎\nRemove Map [Mod+]', value='Removes a map from the map pool\n(Usage: =delmap [name])')
    embed.add_field(name=' ‎\nUnRegister [Mod+]', value='Unregister an user\n(Usage: =unreg [@user])')
    embed.add_field(name=' ‎\nClear Queue [Mod+]', value='Clears the current queue\n(Usage: =clear)')
    embed.add_field(name=' ‎\nForce Rename [Mod+]', value='Renames the user\n(Usage: =fr [@user] [new name])')
    embed.add_field(name=' ‎\nForce Join [Mod+]', value='Adds an user to the queue\n(Usage: =fj [@user])')
    embed.add_field(name=' ‎\nForce Leave [Mod+]', value='Removes an user from the queue\n(Usage: =fl [@user])')
    embed.add_field(name=' ‎\nForce Start [Mod+]', value='Force starts the queue\n(Usage: =fs)')
    embed2.add_field(name=' ‎\nMatch Report [Mod+]', value='Reports a match\n(Usage: =match report [match id] [orange/blue])')
    embed2.add_field(name=' ‎\nMatch Cancel [Mod+]', value='Cancels a match\n(Usage: =match cancel [match id])')
    embed2.add_field(name=' ‎\nMatch Undo [Mod+]', value='Undos a match\n(Usage: =match undo [match id])')
    embed2.add_field(name=' ‎\nReplace [Admin+]', value='Sub players in a match\n(Usage: =sub [match id] [user 1] [user 2])')
    embed2.add_field(name=' ‎\nReset Stats [Admin+]', value='Reset an users stats\n(Usage: =match cancel [match id])')
    embed2.add_field(name=' ‎\nSet Elo [Admin+]', value='Sets an users elo\n(Usage: =setelo @user [amount])')
    embed2.add_field(name=' ‎\nSet Wins [Admin+]', value='Sets an users wins\n(Usage: =setwins @user [amount])')
    embed2.add_field(name=' ‎\nSet Losses [Admin+]', value='Sets an users losses\n(Usage: =setloss @user [amount])')
    embed2.add_field(name=' ‎\nSettings Panel [Admin+]', value='Open Settings Panel\n(Usage: =settings)')
    await ctx.author.send(embed=embed)
    await ctx.author.send(embed=embed2)



client.run('ODgzMDA2NjA5MjgwODY0MjU3.YTDp_Q.Ri7kTw9cAurx0XiGSp-p7qBXICk')