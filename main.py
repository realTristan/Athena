from discord.ext import commands
from discord_components import *
from _sql import *
import discord, os

intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True)
client = commands.Bot(command_prefix='=', intents=intents)
client.remove_command('help')

# // SORT COMMAND DESCRIPTIONS
# ////////////////////////////////
async def _sort_commands():
    cogs=[]; cmds={}
    for command in client.commands:
        cogs.append(command.cog)

    for c in list(cmds.fromkeys(cogs)):
        if c is not None:
            for i in list(cmds.fromkeys(c.get_commands())):
                cmds[i.name] = i.description
    return cmds

# // GET THE SIMILAR COMMANDS TO AN UNKNWON COMMAND
# ////////////////////////////////////////////////////
async def _similar_cmds(ctx):
    correct_commands = await _sort_commands()
    similar_commands=""
    correct_usages = ""
    commands = {}

    for cmd in client.commands:
        for c in str(cmd):
            if c in list(ctx.message.content):
                if str(cmd) not in commands:
                    commands[str(cmd)] = 0
                commands[str(cmd)] += 1

    for s in commands:
        if commands[s] > round(len(list(s))/2):
            similar_commands+=s+"\n"
            correct_usages+=f"{s}: {correct_commands[s]}\n"
    
    if len(similar_commands.split("\n")) < 2:
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} we could not find the command you are looking for", color=15158588))
    return [similar_commands, correct_usages]

# // RETURN THE ERROR EMBED
# //////////////////////////////
async def _error_embed(ctx):
    values = await _similar_cmds(ctx)
    embed=discord.Embed(title=f"Unknown Command: [{ctx.message.content}]", description="**Similar Commands:**\n"+values[0]+"\n**Command Usages:**\n"+values[1], color=15158588)
    embed.set_footer(text="Message \"tristan#2230\" for support")
    return await ctx.send(embed=embed)

# ON COMMAND ERROR HANDLING
# ///////////////////////////////
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        return await ctx.send(embed=discord.Embed(descriptionb=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
    await _error_embed(ctx)
    if not isinstance(error, commands.CommandNotFound):
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