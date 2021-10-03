from discord.ext.commands import has_permissions
import discord, sqlite3, random, time
from discord.ext import commands

db = sqlite3.connect('main.db')
cur = db.cursor()

class Queue(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data = {}

    async def check(self, guild):
        if guild.id not in self.data:
            self.data[guild.id] = {"queue": [], "blue_cap": "", "blue_team": [], "orange_cap": "", "orange_team": [], "pick_logic": [], "maps": [], "state": "queue"}
        return True

    async def on_join(self, guild, user):
        if await self.check(guild):
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {guild.id} AND user_id = {user.id});").fetchall()[0] == (0,):
                for row in cur.execute(f'SELECT * FROM bans WHERE guild_id = {guild.id} AND user_id = {user.id}'):
                    if row[2] - time.time() > 0:
                        return
                    
            if not user in self.data[guild.id]["queue"]:
                self.data[guild.id]["queue"].append(user)
                if len(self.data[guild.id]["queue"]) >= 10:
                    self.data[guild.id]["state"] = "pick"
                    self.data[guild.id]["blue_cap"] = random.choice(self.data[guild.id]["queue"]); self.data[guild.id]["queue"].remove(self.blue_cap)
                    self.data[guild.id]["orange_cap"] = random.choice(self.data[guild.id]["queue"]); self.data[guild.id]["queue"].remove(self.orange_cap)
                    self.data[guild.id]["pick_logic"] = [
                        self.data[guild.id]["blue_cap"], self.data[guild.id]["orange_cap"], self.data[guild.id]["orange_cap"], self.data[guild.id]["blue_cap"],  
                        self.data[guild.id]["blue_cap"], self.data[guild.id]["orange_cap"], self.data[guild.id]["blue_cap"], self.data[guild.id]["orange_cap"],
                    ]
                return True
    
    async def on_leave(self, guild, user):
        if await self.check(guild):
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {guild.id} AND user_id = {user.id});").fetchall()[0] == (0,):
                if user in self.data[guild.id]["queue"]:
                    self.data[guild.id]["queue"].remove(user)
                    return True


    async def embed_gen(self, guild):
        if self.data[guild.id]["state"] == "queue":
            pass
        if self.data[guild.id]["state"] == "pick":
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
                    await ctx.send(await self.embed_gen())
                    self.data[ctx.guild.id]["queue"].clear()
            

    @commands.command(aliases=["j"])
    async def join(self, ctx):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.message.guild.id} AND user_id = {ctx.author.id});").fetchall()[0] == (1,):
            if await self.on_join(ctx.guild, ctx.author):
                await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id]['queue'])}/10]** {ctx.author.mention} has joined the queue", color=65535))

    @commands.command(aliases=["fj"])
    async def forcejoin(self, ctx, user:discord.Member):
        if await self.on_join(ctx.guild, user):
            await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id]['queue'])}/10]** {ctx.author.mention} has added {user.mention} to the queue", color=65535))

    @commands.command(aliases=["l"])
    async def leave(self, ctx):
        if await self.on_leave(ctx.guild, ctx.author):
            await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id]['queue'])}/10]** {ctx.author.mention} has left the queue", color=65535))

    @commands.command(aliases=["fl"])
    async def forceleave(self, ctx, user:discord.Member):
        if await self.on_leave(ctx.guild, user):
            await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id]['queue'])}/10]** {ctx.author.mention} has removed {user.mention} from the queue", color=65535))

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        if await self.check(ctx.guild):
            await ctx.send(embed=discord.Embed(title=f"[{len(self.data[ctx.guild.id]['queue'])}/10] Queue", description='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["queue"]), color=65535))
    
    @commands.command()
    @has_permissions(manage_messages=True)
    async def clear(self, ctx):
        self.data[ctx.guild.id]["queue"].clear()
        await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has cleared the queue", color=65535))


def setup(client):
    client.add_cog(Queue(client))