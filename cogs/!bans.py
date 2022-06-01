from discord.ext import commands
from _sql import Cache, SqlData
import datetime as datetime
import discord, time, re

class Bans(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        
    # // Check mod role or mod permissions
    # //////////////////////////////////////////
    async def check_mod_role(self, ctx):
        if await self.check_admin_role(ctx):
            return True
        mod_role = await SqlData.select(f"SELECT mod_role FROM settings WHERE guild_id = {ctx.guild.id}")
        if mod_role is None:
            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an administrator needs to run the **=settings** command", color=15158588))
            return False
        if mod_role[0] == 0:
            return ctx.author.guild_permissions.manage_messages
        return ctx.guild.get_role(mod_role[0]) in ctx.author.roles
    
    # // Check admin role or admin permissions
    # //////////////////////////////////////////
    async def check_admin_role(self, ctx):
        admin_role = await SqlData.select(f"SELECT admin_role FROM settings WHERE guild_id = {ctx.guild.id}")
        if admin_role is None:
            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an administrator needs to run the **=settings** command", color=15158588))
            return False
        if admin_role[0] == 0 or ctx.author.guild_permissions.administrator:
            return ctx.author.guild_permissions.administrator
        return ctx.guild.get_role(admin_role[0]) in ctx.author.roles
    
    
    # // ADD USER TO BAN DATABASE COMMAND
    # /////////////////////////////////////////
    @commands.command(name="ban", description='`=ban (@user) (length) (reason)  |  Lengths: [s (seconds), m (minutes), h (hours), d (days)]`')
    @commands.cooldown(1, 1, commands.BucketType.user)
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
                
                # If the user is already banned
                if Cache.exists(table="bans", guild=ctx.guild.id, key=user.id):
                    data:list = Cache.fetch(table="bans", guild=ctx.guild.id, key=user.id)
                    return await ctx.send(embed=discord.Embed(title=f"{user.name} banned", description=f"**Length:** {datetime.timedelta(seconds=data[0])}\n**Reason:** {data[1]}\n**Banned by:** {data[2]}", color=15158588))
                
                # Ban the user
                ban_time = length+time.time()
                ban_reason = ' '.join(str(e) for e in args)
                await Cache.update(
                    table="bans", guild=ctx.guild.id, key=user.id, data=[ban_time, ban_reason, ctx.author.mention],
                    sqlcmd=f"INSERT INTO bans (guild_id, user_id, length, reason, banned_by) VALUES ({ctx.guild.id}, {user.id}, {length + time.time()}, '{' '.join(str(e) for e in args)}', '{ctx.author.mention}')"
                )
                return await ctx.send(embed=discord.Embed(title=f"{user.name} banned", description=f"**Length:** {datetime.timedelta(seconds=ban_time)}\n**Reason:** {ban_reason}\n**Banned by:** {ctx.author.mention}", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

    # // REMOVE USER FROM BAN DATABASE COMMAND
    # /////////////////////////////////////////
    @commands.command(name="unban", description='`=unban (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def unban(self, ctx:commands.Context, user:discord.Member):
        if not ctx.author.bot:
            if await self.check_mod_role(ctx):
                if Cache.exists(table="bans", guild=ctx.guild.id, key=user.id):
                    await Cache.delete(
                        table="bans", guild=ctx.guild.id, key=user.id,
                        sqlcmd=f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"
                    )
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has unbanned {user.mention}", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not banned", color=33023))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))


def setup(client: commands.Bot):
    client.add_cog(Bans(client))