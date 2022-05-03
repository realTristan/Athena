from discord.ext import commands
import datetime as datetime
import discord, time, re
from _sql import *

class Bans(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    # // Check mod role or mod permissions
    # //////////////////////////////////////////
    async def check_mod_role(self, ctx):
        if await self.check_admin_role(ctx):
            return True
        mod_role = await SQL_CLASS().select(f"SELECT mod_role FROM settings WHERE guild_id = {ctx.guild.id}")
        if mod_role is None:
            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an administrator needs to run the **=settings** command", color=15158588))
            return False
        if mod_role[0] == 0:
            return ctx.author.guild_permissions.manage_messages
        return ctx.guild.get_role(mod_role[0]) in ctx.author.roles
    
    # // Check admin role or admin permissions
    # //////////////////////////////////////////
    async def check_admin_role(self, ctx):
        admin_role = await SQL_CLASS().select(f"SELECT admin_role FROM settings WHERE guild_id = {ctx.guild.id}")
        if admin_role is None:
            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an administrator needs to run the **=settings** command", color=15158588))
            return False
        if admin_role[0] == 0 or ctx.author.guild_permissions.administrator:
            return ctx.author.guild_permissions.administrator
        return ctx.guild.get_role(admin_role[0]) in ctx.author.roles
    
    
    # // ADD USER TO BAN DATABASE COMMAND
    # /////////////////////////////////////////
    @commands.command(name="ban", description='`=ban (@user) (length) (reason)  |  Lengths: [s (seconds), m (minutes), h (hours), d (days)]`')
    async def ban(self, ctx:commands.Context, user:discord.Member, length_str:str, *args):
        if not ctx.author.bot:
            if await self.check_mod_role(ctx):
                if "s" in length_str:
                    length = int(re.sub("\D","", length_str))
                if "m" in length_str:
                    length = int(re.sub("\D","", length_str)) * 60
                if "h" in length_str:
                    length = int(re.sub("\D","", length_str)) * 3600
                if "d" in length_str:
                    length = int(re.sub("\D","", length_str)) * 86400
                
                rows = await SQL_CLASS().select(f"SELECT * FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                if rows is not None:
                    await SQL_CLASS().execute(f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                await SQL_CLASS().execute(f"INSERT INTO bans (guild_id, user_id, length, reason, banned_by) VALUES ({ctx.guild.id}, {user.id}, {length + time.time()}, '{' '.join(str(e) for e in args)}', '{ctx.author.mention}')")

                rows = await SQL_CLASS().select(f"SELECT * FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                return await ctx.send(embed=discord.Embed(title=f"{user.name} banned", description=f"**Length:** {datetime.timedelta(seconds=int(rows[2] - time.time()))}\n**Reason:** {rows[3]}\n**Banned by:** {rows[4]}", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

    # // REMOVE USER FROM BAN DATABASE COMMAND
    # /////////////////////////////////////////
    @commands.command(name="unban", description='`=unban (@user)`')
    async def unban(self, ctx:commands.Context, user:discord.Member):
        if not ctx.author.bot:
            if await self.check_mod_role(ctx):
                if await SQL_CLASS().exists(f"SELECT * FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
                    await SQL_CLASS().execute(f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has unbanned {user.mention}", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not banned", color=33023))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))


def setup(client):
    client.add_cog(Bans(client))