from discord.ext import commands
import discord, sqlite3, time
import datetime as datetime

class Bans(commands.Cog):
    def __init__(self, client):
        self.client = client

    # // ADD USER TO BAN DATABASE COMMAND
    # /////////////////////////////////////////
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def ban(self, ctx, user:discord.Member, length_str:str, *args):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if "s" in length_str:
                length = int(length_str.strip("s"))
            if "m" in length_str:
                length = int(length_str.strip("m")) * 60
            if "h" in length_str:
                length = int(length_str.strip("h")) * 3600
            if "d" in length_str:
                length = int(length_str.strip("d")) * 86400
            
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                cur.execute(f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id};")
            cur.execute(f"INSERT INTO bans VALUES ({ctx.guild.id}, {user.id}, {length + time.time()}, '{' '.join(str(e) for e in args)}', '{ctx.author.mention}')")
            db.commit()
            for row in cur.execute(f'SELECT * FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                return await ctx.send(embed=discord.Embed(title=f"{user.name} banned", description=f"**Length:** {datetime.timedelta(seconds=int(row[2] - time.time()))}\n**Reason:** {row[3]}\n**Banned by:** {row[4]}", color=65535))

    # // REMOVE USER FROM BAN DATABASE COMMAND
    # /////////////////////////////////////////
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def unban(self, ctx, user:discord.Member):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                cur.execute(f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id};")
                db.commit()
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has unbanned {user.mention}", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not banned", color=65535))


def setup(client):
    client.add_cog(Bans(client))