from discord.ext import commands
import datetime as datetime
import discord, time, re
from data import *

# // Bans cog
class Bans(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        
    # // Check mod role or mod permissions
    # //////////////////////////////////////////
    async def check_mod_role(self, ctx: commands.Context):
        # // If the user has admin role, return true
        if await self.check_admin_role(ctx):
            return True
        
        # // Else, check for whether the user has mod role
        mod_role = Settings(ctx.guild.id).get("mod_role")
        return ctx.guild.get_role(mod_role) in ctx.author.roles
    
    
    # // Check admin role or admin permissions
    # //////////////////////////////////////////
    async def check_admin_role(self, ctx: commands.Context):
        # // Get the admin role from settings
        admin_role = Settings(ctx.guild.id).get("admin_role")
        
        # // Check admin permissions
        if admin_role == 0 or ctx.author.guild_permissions.administrator:
            return ctx.author.guild_permissions.administrator
        return ctx.guild.get_role(admin_role) in ctx.author.roles
    
    
    # Add an user to the ban database command
    @commands.command(name="ban", description='`=ban (@user) (length) (reason)  |  Lengths: [s (seconds), m (minutes), h (hours), d (days)]`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def ban(self, ctx:commands.Context, user:discord.Member, length_str:str, *args):
        if ctx.author.bot:
            return
        
        # // Check if the user has enough permissions
        if not await self.check_mod_role(ctx):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
        # // Get the ban length
        if "s" in length_str:
            length = int(re.sub("\D","", length_str))
        if "m" in length_str:
            length = int(re.sub("\D","", length_str)) * 60
        if "h" in length_str:
            length = int(re.sub("\D","", length_str)) * 3600
        if "d" in length_str:
            length = int(re.sub("\D","", length_str)) * 86400
        
        # // Chekc if the user already exists in the bans table
        if Bans(ctx.guild.id).is_banned(user.id):
            # // Get the ban data
            ban_data = Bans(ctx.guild.id).get(user.id)

            # // If the users ban time hasn't expired yet
            if ban_data[0] - time.time() > 0:
                return await ctx.send(embed=discord.Embed(title=f"{user.name} already banned", description=f"**Length:** {datetime.timedelta(seconds=ban_data[0])}\n**Reason:** {ban_data[1]}\n**Banned by:** {ban_data[2]}", color=15158588))
            else:
                # // Unban the user
                await Bans(ctx.guild.id).unban(user.id)
                
        # // Ban the user (time, reason)
        ban_time = int(length+time.time())
        ban_reason = ' '.join(str(e) for e in args)
        
        # // Ban the user
        await Bans(ctx.guild.id).ban(user.id, ban_time, ban_reason, ctx.author.id)
        
        # // Send the embeds
        await ctx.send(embed=discord.Embed(title=f"{user.name} banned", description=f"**Length:** {datetime.timedelta(seconds=int(ban_time-time.time()))}\n**Reason:** {ban_reason}\n**Banned by:** {ctx.author.mention}", color=15158588))


    # Remove an user from the ban database command
    @commands.command(name="unban", description='`=unban (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def unban(self, ctx:commands.Context, user:discord.Member):
        if ctx.author.bot:
            return
        
        # // Check if the user has mod role
        if not await self.check_mod_role(ctx):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
        # // If the user exists in the bans cache and database
        if not Bans(ctx.guild.id).is_banned(user.id):
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not banned", color=33023))
        
        # // Unban the user
        await Bans(ctx.guild.id).unban(user.id)
        
        # // Send the embed
        await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has unbanned {user.mention}", color=3066992))


def setup(client: commands.Bot):
    client.add_cog(Bans(client))