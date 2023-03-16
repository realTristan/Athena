from cache import Cache, Settings, Users, Database
from discord.ext import commands
from discord_components import *
import discord, os

# // CREATE THE CLIENT
CLIENT: commands.Bot = commands.Bot(
    help_command = None,
    command_prefix = '=', 
    intents = discord.Intents(
        message_content = True,
        presences = True,
        messages = True,
        members = True,
        guilds = True
    )
)

# // REMOVE MEMBER FROM DATABASE WHEN THEY LEAVE THE SERVER
# //////////////////////////////////////////////////////////////
@CLIENT.event
async def on_member_remove(member: discord.Member):
    if Users.exists(member.guild.id, member.id):
        Users.delete(member.guild.id, member.id)

# // ON GUILD JOIN
# ////////////////////
@CLIENT.event
async def on_guild_join(guild: discord.Guild):
    # // Create the settings
    if not Settings.exists(guild.id):
        Settings.setup(guild.id)

    # // Update server count
    await CLIENT.change_presence(
        activity = discord.Activity(
            type = discord.ActivityType.watching, 
            name = f"{len(CLIENT.guilds)} Servers"
    ))
    
# // ON BOT LAUNCH
# ///////////////////
@CLIENT.event
async def on_ready():
    # // Load the database
    # await Database.reset()

    # // Load the cache
    await Cache.load_data()

    # // Load the discord components
    DiscordComponents(CLIENT)

    # // Confirm Launch
    print(f'{CLIENT.user.name} ({CLIENT.user.id}) is now running.')
    await CLIENT.change_presence(
        activity = discord.Activity(
            type = discord.ActivityType.watching, 
            name = f"{len(CLIENT.guilds)} Servers"
    ))

    # // Load the cogs
    for filename in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cogs')):
        if filename.endswith('.py'):
            CLIENT.load_extension(f'cogs.{filename[:-3]}')
            print(f'Loaded: cog.{filename[:-3]}')


# // Run the client
CLIENT.run('YOUR BOT TOKEN')
