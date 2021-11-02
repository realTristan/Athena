from discord.ext import commands
from discord_components import *
from _sql import *
import discord, os

intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True)
client = commands.Bot(command_prefix='=', intents=intents)
client.remove_command('help')

# // GET THE SIMILAR COMMANDS TO AN UNKNWON COMMAND
# ////////////////////////////////////////////////////
async def _similar_cmds(ctx):
    similar_commands=""; dict = {}
    for command in client.commands:
        for c in str(command):
            if c in list(ctx.message.content):
                if str(command) not in dict:
                    dict[str(command)] = 0
                dict[str(command)] += 1

    for s in dict:
        if dict[s] > round(len(list(s))/2):
            similar_commands+=s+"\n"
    
    if len(similar_commands.split("\n")) < 2:
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} we could not find the command you are looking for", color=15158588))
    return await ctx.send(embed=discord.Embed(title=f"Unknown Command: [{ctx.message.content}]", description="**Similar commands:**\n"+similar_commands, color=15158588))

# ON COMMAND ERROR HANDLING
# ///////////////////////////////
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return await _similar_cmds(ctx)
    if isinstance(error, commands.MissingPermissions):
        return
    embed=discord.Embed(title=f"Internal Error", description=f"{error}", color=15158588)
    embed.set_footer(text="Message \"tristan#2230\" for support")
    await ctx.send(embed=embed)
    raise error
    
# // REMOVE MEMBER FROM DATABASE WHEN THEY LEAVE THE SERVER
# //////////////////////////////////////////////////////////////
@client.event
async def on_member_remove(member):
    if await SQL_CLASS().exists(f"SELECT * FROM users WHERE guild_id = {member.guild.id} AND user_id = {member.id}"):
        await SQL_CLASS().execute(f"DELETE FROM users WHERE guild_id = {member.guild.id} AND user_id = {member.id}")

# // ON BOT LAUNCH
# ///////////////////
@client.event
async def on_ready():
    DiscordComponents(client)
    print(f'Launched: {client.user.name} // {client.user.id}')
    await client.change_presence(activity=discord.Game(name="Ten Man's | =help"))

    # // LOAD THE COGS
    for filename in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cogs')):
        if filename.endswith('.py'):
            client.load_extension(f'cogs.{filename[:-3]}')
            print(f'Loaded: cog.{filename[:-3]}')


client.run('YOUR BOT TOKEN')