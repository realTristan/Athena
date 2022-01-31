from discord.ext import commands
from _sql import *
import discord

class Dev(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.dev_users = [
            395645581067943936
        ]

    # // EDIT AN USERS NAME OR ROLE FUNCTION
    # ////////////////////////////////////////
    async def _user_edit(self, user, nick=None, role=None):
        try:
            if nick is not None:
                await user.edit(nick=nick)

            if role is not None:
                await user.add_roles(role)
        except Exception as e:
            print(e)
            
    # // REGISTER USER INTO THE DATABASE FUNCTION
    # ///////////////////////////////////////////////
    async def _register_user(self, ctx, user, name, role):
        await SQL_CLASS().execute(f"INSERT INTO users (guild_id, user_id, user_name, elo, wins, loss) VALUES ({ctx.guild.id}, {user.id}, '{name}', 0, 0, 0)")
        if role not in user.roles:
            await self._user_edit(user, role=role)

    # // REGISTER EVERY SERVER MEMBER COMMAND
    # //////////////////////////////////////////
    @commands.command(description='`Only "tristan#2230" has access to this command`')
    @commands.has_permissions(administrator=True)
    async def _reg_all(self, ctx):
        if ctx.author.id in self.dev_users:
            settings = await SQL_CLASS().select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
            role = None
            if settings[1] != 0:
                role = ctx.guild.get_role(settings[1])

            for user in ctx.guild.members:
                if not user.bot:
                    if not await SQL_CLASS().exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
                        await self._register_user(ctx, user, user.name, role)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has registered every member", color=3066992))
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
    
    # // UNREGISTER EVERY SERVER MEMBER COMMAND
    # //////////////////////////////////////////
    @commands.command(description='`Only "tristan#2230" has access to this command`')
    @commands.has_permissions(administrator=True)
    async def _unreg_all(self, ctx):
        if ctx.author.id in self.dev_users:
            for user in ctx.guild.members:
                if await SQL_CLASS().exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
                    await SQL_CLASS().execute(f"DELETE FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has unregistered every member", color=3066992))
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

def setup(client):
    client.add_cog(Dev(client))