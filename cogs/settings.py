from discord.ext.commands import has_permissions
from discord.ext import commands
import discord, sqlite3

db = sqlite3.connect('main.db')
cur = db.cursor()

class Settings(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @has_permissions(administrator=True)
    async def addmap(self, ctx, map:str):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM maps WHERE guild_id = {ctx.guild.id});").fetchall()[0] == (0,):
            cur.execute(f"INSERT INTO maps VALUES ({ctx.guild.id}, '{map}')")
        else:
            for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
                if map not in str(row[1]).split(","):
                    cur.execute(f"UPDATE maps SET map_list = '{str(row[1])},{map}' WHERE guild_id = {ctx.guild.id}")
        db.commit()
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} added **{map}** to the map pool", color=65535))

    @commands.command(aliases=["removemap", "deletemap"])
    @has_permissions(administrator=True)
    async def delmap(self, ctx, map:str):
        for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
            if map in str(row[1]).split(","):
                map_list = str(row[1]).split(',')
                map_list.remove(map)
                cur.execute(f"UPDATE maps SET map_list = '{','.join(str(e) for e in map_list)}' WHERE guild_id = {ctx.guild.id}")
                db.commit()
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} removed **{map}** from the map pool", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} **{map}** is not in the map pool", color=65535))

    @commands.command()
    async def maps(self, ctx):
        for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
            return await ctx.send(embed=discord.Embed(title="Maps", description=str(row[1]).replace(",", "\n"), color=65535))

    @commands.command()
    @has_permissions(administrator=True)
    async def regrole(self, ctx, role:discord.Role):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM reg_role WHERE guild_id = {ctx.guild.id});").fetchall()[0] == (0,):
            return cur.execute(f"INSERT INTO reg_role VALUES ({ctx.guild.id}, {role.id})")
        else:
            cur.execute(f"UPDATE reg_role SET role_id = {role.id} WHERE guild_id = {ctx.guild.id}")
        db.commit()
        return await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} set {role.mention} as the register role', color=65535))




def setup(client):
    client.add_cog(Settings(client))