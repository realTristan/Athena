from discord.ext import commands
from discord_components import *
from _sql import *
import discord, os

intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True)
client = commands.Bot(command_prefix='=', intents=intents)
client.remove_command('help')

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        return
    await ctx.send(embed=discord.Embed(title=f"Internal Error", url="https://discord.gg/ZpP5eNWKwr", description=f"{error}", color=15158588))
    raise error
    
@client.event
async def on_member_remove(member):
    if await SQL_CLASS().exists(f"SELECT * FROM users WHERE guild_id = {member.guild.id} AND user_id = {member.id}"):
        await SQL_CLASS().execute(f"DELETE FROM users WHERE guild_id = {member.guild.id} AND user_id = {member.id}")


@client.event
async def on_ready():
    DiscordComponents(client)
    print(f'Launched: {client.user.name} // {client.user.id}')
    await client.change_presence(activity=discord.Game(name="Ten Man's | =help"))

for filename in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cogs')):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')
        print(f'Loaded: cog.{filename[:-3]}')


client.run('ODgzMDA2NjA5MjgwODY0MjU3.YTDp_Q.kbpZyDSZPOJ_XQEq06FW86U8yJo')