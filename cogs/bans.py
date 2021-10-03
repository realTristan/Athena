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
        try:
            if time[len(time)] == "m":
                length = int(time.strip("m")) * 60
            if time[len(time)] == "h":
                length = int(time.strip("h")) * 3600
            if time[len(time)] == "d":
                length = int(time.strip("d")) * 86400
                
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user});").fetchall()[0] == (0,):
                cur.execute(f"INSERT INTO bans VALUES ({ctx.guild.id}, {ctx.author.id}, {length}, '{reason}', '{ctx.author}'")
                db.commit()
                await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has banned **{user.mention} for **{time}**", color=65535))
        except Exception as e:
            await ctx.send(embed=discord.Embed(title="Error", description=e, color=65535))

    async def unban(self, ctx, user:discord.Member):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user});").fetchall()[0] == (0,):
                cur.execute(f"DELETE FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});")
                db.commit()
                await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has unbanned **{user.mention}", color=65535))


def setup(client):
    client.add_cog(Bans(client))