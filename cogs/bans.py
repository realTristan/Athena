from discord.ext.commands import has_permissions
from discord.ext import commands
import discord, sqlite3

db = sqlite3.connect('main.db')
cur = db.cursor()

class Bans(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.command()
    async def ban(self, ctx, user:discord.Member, time:str, reason:str):
        if "s" in time:
            length = int(time.strip("s"))
        if "m" in time:
            length = int(time.strip("m")) * 60
        if "h" in time:
            length = int(time.strip("h")) * 3600
        if "d" in time:
            length = int(time.strip("d")) * 86400
            
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (0,):
            cur.execute(f"INSERT INTO bans VALUES ({ctx.guild.id}, {ctx.author.id}, {length}, '{reason}', '{ctx.author}')")
            db.commit()
            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has banned {user.mention} for **{time}**", color=65535))


    @commands.command()
    async def unban(self, ctx, user:discord.Member):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
            cur.execute(f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id};")
            db.commit()
            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has unbanned {user.mention}", color=65535))


def setup(client):
    client.add_cog(Bans(client))