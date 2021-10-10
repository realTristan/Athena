from discord.ext import commands
import discord, sqlite3, time
import datetime as datetime

db = sqlite3.connect('main.db')
cur = db.cursor()

class Bans(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def ban(self, ctx, user:discord.Member, length_str:str, reason:str):
        if "s" in length_str:
            length = int(length_str.strip("s"))
        if "m" in length_str:
            length = int(length_str.strip("m")) * 60
        if "h" in length_str:
            length = int(length_str.strip("h")) * 3600
        if "d" in length_str:
            length = int(length_str.strip("d")) * 86400
        
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
            for row in cur.execute(f'SELECT * FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                if row[2] - time.time() <= 0:
                    cur.execute(f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id};")
        else:
            cur.execute(f"INSERT INTO bans VALUES ({ctx.guild.id}, {user.id}, {length + time.time()}, '{reason}', '{ctx.author.mention}')")
            db.commit()
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has banned {user.mention} for **{length_str}**", color=65535))
            
        for row in cur.execute(f'SELECT * FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
            return await ctx.send(embed=discord.Embed(title=f"{user.name} is banned", description=f"**Length:** {datetime.timedelta(seconds=int(row[2] - time.time()))}\n**Reason:** {row[3]}\n**Banned by:** {row[4]}", color=65535))


    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def unban(self, ctx, user:discord.Member):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
            cur.execute(f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id};")
            db.commit()
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has unbanned {user.mention}", color=65535))
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not banned", color=65535))


def setup(client):
    client.add_cog(Bans(client))