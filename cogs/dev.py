from discord.ext import commands
from _sql import *
import discord
SQL = SQL()

class Dev(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.dev_users = [
            395645581067943936
        ]

    # // REGISTER USER INTO THE DATABASE FUNCTION
    # ///////////////////////////////////////////////
    async def _register_user(self, ctx, user, name, role):
        await SQL.execute(f"INSERT INTO users (guild_id, user_id, user_name, elo, wins, loss) VALUES ({ctx.guild.id}, {user.id}, '{name}', 0, 0, 0)")
        if role not in user.roles:
            await self._user_edit(user, role=role)

    # // REGISTER EVERY SERVER MEMBER COMMAND
    # //////////////////////////////////////////
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def _reg_all(self, ctx):
        if ctx.author.id in self.dev_users:
            # // REGISTER EVERY MEMBER IN THE SERVER
            settings = await SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")

            # // GETTING THE REGISTER ROLE FROM SETTINGS
            role = None
            if settings[1] != 0:
                role = ctx.guild.get_role(settings[1])

            for user in ctx.guild.members:
                if not user.bot:
                    if not await SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
                        await self._register_user(ctx, user, user.name, role)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has registered every member", color=3066992))
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
    
    # // UNREGISTER EVERY SERVER MEMBER COMMAND
    # //////////////////////////////////////////
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def _unreg_all(self, ctx):
        if ctx.author.id in self.dev_users:
            for user in ctx.guild.members:
                if await SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
                    await SQL.execute(f"DELETE FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has unregistered every member", color=3066992))
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

def setup(client):
    client.add_cog(Dev(client))