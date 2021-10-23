from discord.ext import commands
import datetime as datetime
import discord, time
from _sql import *
SQL = SQL()


class Bans(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.dev_users = [
            395645581067943936
        ]

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
    client.add_cog(Bans(client))