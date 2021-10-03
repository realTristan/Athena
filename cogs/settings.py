from discord.ext.commands import has_permissions
from discord.ext import commands
import discord, json

class Settings(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def write(self, file, data):
        with open(f"json/{file}.json", "w") as f:
            json.dump(data, f, indent=4)

    @commands.command()
    @has_permissions(administrator=True)
    async def addmap(self, ctx, map:str):
        data=json.load(open("json/maps.json", "r+"))
        if ctx.guild.id not in data:
            data[ctx.guild.id] = []
        if map not in data[ctx.guild.id]["maps"]:
            data[ctx.guild.id]["maps"].append(map)
            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} added **{map}** to the map pool", color=65535))
            await self.write("maps", data)

    @commands.command(aliases=["removemap", "deletemap"])
    @has_permissions(administrator=True)
    async def delmap(self, ctx, map:str):
        data=json.load(open("json/maps.json", "r+"))
        if ctx.guild.id not in data:
            data[ctx.guild.id] = []
        if map in data[ctx.guild.id]["maps"]:
            data[ctx.guild.id]["maps"].remove(map)
            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} removed **{map}** from the map pool", color=65535))
            await self.write("maps", data)



def setup(client):
    client.add_cog(Settings(client))