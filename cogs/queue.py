from discord.ext.commands import has_permissions
import discord, sqlite3, random, time, json
from discord.ext import commands
import datetime as datetime

db = sqlite3.connect('main.db')
cur = db.cursor()

class Queue(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data = {}

    async def check_data(self, guild):
        if guild.id not in self.data:
            self.data[guild.id] = {"queue": [], "blue_cap": "", "blue_team": [], "orange_cap": "", "orange_team": [], "pick_logic": [], "map": "", "state": "queue"}
        return True

    async def on_join(self, guild, user):
        if await self.check_data(guild):
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                for row in cur.execute(f'SELECT * FROM bans WHERE guild_id = {guild.id} AND user_id = {user.id}'):
                    if row[2] - time.time() > 0:
                        return discord.Embed(title=f"{user.name} is banned", description=f"**Length:** {datetime.timedelta(seconds=int(row[2] - time.time()))}\n**Reason:** {row[3]}\n**Banned by:** {row[4]}", color=65535)

            if not user in self.data[guild.id]["queue"]:
                self.data[guild.id]["queue"].append(user)
                if len(self.data[guild.id]["queue"]) >= 10:
                    self.data[guild.id]["state"] = "pick"
                    self.data[guild.id]["blue_cap"] = random.choice(self.data[guild.id]["queue"]); self.data[guild.id]["queue"].remove(self.blue_cap)
                    self.data[guild.id]["orange_cap"] = random.choice(self.data[guild.id]["queue"]); self.data[guild.id]["queue"].remove(self.orange_cap)
                    self.data[guild.id]["pick_logic"] = [
                        self.data[guild.id]["blue_cap"], self.data[guild.id]["orange_cap"], self.data[guild.id]["orange_cap"], self.data[guild.id]["blue_cap"],
                        self.data[guild.id]["blue_cap"], self.data[guild.id]["orange_cap"], self.data[guild.id]["blue_cap"], self.data[guild.id]["orange_cap"]]
                    return await self.embed_gen(guild)
                return discord.Embed(description=f"**[{len(self.data[guild.id]['queue'])}/10]** {user.mention} has joined the queue", color=65535)
    
    async def on_leave(self, guild, user):
        if await self.check_data(guild):
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {guild.id} AND user_id = {user.id});").fetchall()[0] == (0,):
                if user in self.data[guild.id]["queue"]:
                    self.data[guild.id]["queue"].remove(user)
                    return discord.Embed(description=f"**[{len(self.data[guild.id]['queue'])}/10]** {user.mention} has left the queue", color=65535)

    async def embed_gen(self, guild):
        if self.data[guild.id]["state"] == "queue":
            return discord.Embed(title=f"[{len(self.data[guild.id]['queue'])}/10] Queue", description='\n'.join(str(e.mention) for e in self.data[guild.id]["queue"]), color=65535)
        if self.data[guild.id]["state"] == "pick":
            pass
        if self.data[guild.id]["state"] == "maps":
            pass
        if self.data[guild.id]["state"] == "final":
            pass


    @commands.command(aliases=["p"])
    async def pick(self, ctx, user):
        if self.data[ctx.guild.id]["state"] == "pick":
            if ctx.author == self.data[ctx.guild.id]["pick_logic"].pop(0):
                if self.data[ctx.guild.id]["blue_cap"] == ctx.author:
                    self.data[ctx.guild.id]["blue_team"].append(user)
                    self.data[ctx.guild.id]["queue"].remove(user)
                else:
                    self.data[ctx.guild.id]["blue_team"].append(user)
                    self.data[ctx.guild.id]["queue"].remove(user)
                await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has picked {user.mention}", color=65535))
                
                if len(self.data[ctx.guild.id]["queue"]) >= 0:
                    self.data[ctx.guild.id]["state"] = "maps"
                    await ctx.send(await self.embed_gen(ctx.guild))
                    self.data[ctx.guild.id]["queue"].clear()
    
    @commands.command()
    async def map(self, ctx, map:str):
        if ctx.author == self.data[ctx.guild.id]["blue_cap"]:
            maps=json.load(open("json/maps.json", "r+"))
            if map in maps[ctx.guild.id]:
                self.data[ctx.guild.id]["map"] = map
                self.data[ctx.guild.id]["state"] = "final"
                await ctx.send(await self.embed_gen(ctx.guild))
            
    @commands.command(aliases=["j"])
    async def join(self, ctx):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id});").fetchall()[0] == (1,):
            await ctx.send(embed=await self.on_join(ctx.guild, ctx.author))

    @commands.command(aliases=["fj"])
    async def forcejoin(self, ctx, user:discord.Member):
        await ctx.send(embed=await self.on_join(ctx.guild, user))

    @commands.command(aliases=["l"])
    async def leave(self, ctx):
        await ctx.send(embed=await self.on_leave(ctx.guild, ctx.author))

    @commands.command(aliases=["fl"])
    async def forceleave(self, ctx, user:discord.Member):
        await ctx.send(embed=await self.on_leave(ctx.guild, user))

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        if await self.check_data(ctx.guild):
            await ctx.send(embed=await self.embed_gen(ctx.guild))
    
    @commands.command()
    @has_permissions(manage_messages=True)
    async def clear(self, ctx):
        self.data[ctx.guild.id]["queue"].clear()
        await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has cleared the queue", color=65535))


def setup(client):
    client.add_cog(Queue(client))