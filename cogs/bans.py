from discord.ext import commands
import datetime as datetime
import discord, time
from _sql import *
SQL = SQL()


class Bans(commands.Cog):
    def __init__(self, client):
        self.client = client

    # // ADD USER TO BAN DATABASE COMMAND
    # /////////////////////////////////////////
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def ban(self, ctx, user:discord.Member, length_str:str, *args):
        if "s" in length_str:
            length = int(length_str.strip("s"))
        if "m" in length_str:
            length = int(length_str.strip("m")) * 60
        if "h" in length_str:
            length = int(length_str.strip("h")) * 3600
        if "d" in length_str:
            length = int(length_str.strip("d")) * 86400
        
        if SQL.exists(f"SELECT * FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
            SQL.execute(f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")

        SQL.execute(f"INSERT INTO bans (guild_id, user_id, length, reason, banned_by) VALUES ({ctx.guild.id}, {user.id}, {length + time.time()}, '{' '.join(str(e) for e in args)}', '{ctx.author.mention}')")
        rows = SQL.select(f"SELECT * FROM bans WHERE user_id = {user.id} AND guild_id = {ctx.guild.id}")
        return await ctx.channel.send(embed=discord.Embed(title=f"{user.name} banned", description=f"**Length:** {datetime.timedelta(seconds=int(rows[2] - time.time()))}\n**Reason:** {rows[3]}\n**Banned by:** {rows[4]}", color=9961472))


    # // REMOVE USER FROM BAN DATABASE COMMAND
    # /////////////////////////////////////////
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def unban(self, ctx, user:discord.Member):
        if SQL.exists(f"SELECT * FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
            SQL.execute(f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} has unbanned {user.mention}", color=65280))
        return await ctx.channel.send(embed=discord.Embed(description=f"{user.mention} is not banned", color=33023))


def setup(client):
    client.add_cog(Bans(client))