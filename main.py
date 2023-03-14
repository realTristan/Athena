from discord.ext import commands
from discord_components import *
from data import *
import discord, os

client = commands.Bot(
    help_command=None,
    command_prefix='=', 
    intents=discord.Intents(
        message_content=True,
        presences=True,
        messages=True,
        members=True,
        guilds=True
    )
)

# // REMOVE MEMBER FROM DATABASE WHEN THEY LEAVE THE SERVER
# //////////////////////////////////////////////////////////////
@client.event
async def on_member_remove(member):
    if User(member.guild.id, member.id).exists():
        User(member.guild.id, member.id).delete()

# // ON GUILD JOIN
# ////////////////////
@client.event
async def on_guild_join(guild):
    # // Create the settings
    if not Settings(guild.id).exists():
        Settings(guild.id).setup()

    # // Update server count
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(client.guilds)} Servers"))
    
# // ON BOT LAUNCH
# ///////////////////
@client.event
async def on_ready():
    await Cache.load_data()
    DiscordComponents(client)
    print(f'Launched: {client.user.name} // {client.user.id}')
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(client.guilds)} Servers"))

    # // LOAD THE COGS
    for filename in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cogs')):
        if filename.endswith('.py'):
            client.load_extension(f'cogs.{filename[:-3]}')
            print(f'Loaded: cog.{filename[:-3]}')

client.run('YOUR BOT TOKEN')
