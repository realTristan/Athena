from discord.ext.commands import has_permissions
import discord, sqlite3, random, time
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
    
    async def reset(self, guild):
        self.data[guild.id] = {"queue": [], "blue_cap": "", "blue_team": [], "orange_cap": "", "orange_team": [], "pick_logic": [], "map": "", "state": "queue"}

    async def embed_gen(self, ctx):
        if self.data[ctx.guild.id]["state"] == "queue":
            if len(self.data[ctx.guild.id]["queue"]) == 0:
                current_queue = "None"
            else:
                current_queue = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["queue"])
            return await ctx.send(embed=discord.Embed(title=f"[{len(self.data[ctx.guild.id]['queue'])}/10] Queue", description=current_queue, color=65535))

        if self.data[ctx.guild.id]["state"] == "pick":
            if len(self.data[ctx.guild.id]["orange_team"]) == 0:
                orange_team = "None"
            else:
                orange_team = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["orange_team"])

            if len(self.data[ctx.guild.id]["blue_team"]) == 0:
                blue_team = "None"
            else:
                blue_team = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["blue_team"])

            embed=discord.Embed(title="Picking Phase", color=65535)
            embed.add_field(name="Orange Captain", value=self.data[ctx.guild.id]["orange_cap"].mention)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=self.data[ctx.guild.id]["blue_cap"].mention)
            embed.add_field(name="Orange Team", value=orange_team)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value=blue_team)
            embed.add_field(name="Available Players", value="\n".join(str(e.mention) for e in self.data[ctx.guild.id]["queue"]))
            await ctx.send(embed=embed)
            return await ctx.send(f"**{self.data[ctx.guild.id]['pick_logic'][0].mention} it is your turn to pick**")

        if self.data[ctx.guild.id]["state"] == "maps":
            for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
                embed=discord.Embed(title="Map Phase", color=65535)
                embed.add_field(name="Orange Captain", value=self.data[ctx.guild.id]["orange_cap"].mention)
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="Blue Captain", value=self.data[ctx.guild.id]["blue_cap"].mention)
                embed.add_field(name="Orange Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["orange_team"]))
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="Blue Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["blue_team"]))
                embed.add_field(name="Available Maps", value=str(row[1]).replace(",", "\n"))
                await ctx.send(embed=embed)
                return await ctx.send(f"**{self.data[ctx.guild.id]['blue_cap'].mention} select a map to play**")

        if self.data[ctx.guild.id]["state"] == "final":
            embed=discord.Embed(title="Final Match Up", description=f"**Map:** {self.data[ctx.guild.id]['map']}", color=65535)
            embed.add_field(name="Orange Captain", value=self.data[ctx.guild.id]["orange_cap"].mention)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=self.data[ctx.guild.id]["blue_cap"].mention)
            embed.add_field(name="Orange Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["orange_team"]))
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["blue_team"]))

            await self.add_match(ctx.guild)
            await self.reset(ctx.guild)
            return await ctx.send(embed=embed)

    async def add_match(self, guild):
        orange_team = ','.join(str(e.id) for e in self.data[guild.id]['orange_team'])
        blue_team = ','.join(str(e.id) for e in self.data[guild.id]['blue_team'])
        match_count=0

        for _ in cur.execute(f'SELECT * FROM matches WHERE guild_id = {guild.id}'):
            match_count+=1
        cur.execute(f"""INSERT INTO matches VALUES ({guild.id}, {match_count}, '{self.data[guild.id]['map']}', '{self.data[guild.id]['orange_cap'].id}', '{orange_team}', '{self.data[guild.id]['blue_cap'].id}', '{blue_team}', 'ongoing')""")
        db.commit()

    async def on_join(self, ctx, user):
        if await self.check_data(ctx.guild):
            if self.data[ctx.guild.id]["state"] == "queue":
                if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                    for row in cur.execute(f'SELECT * FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                        if row[2] - time.time() >= 0:
                            return discord.Embed(title=f"{user.name} is banned", description=f"**Length:** {datetime.timedelta(seconds=int(row[2] - time.time()))}\n**Reason:** {row[3]}\n**Banned by:** {row[4]}", color=65535)
                    cur.execute(f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id};")
                    db.commit()
                if not user in self.data[ctx.guild.id]["queue"]:
                    self.data[ctx.guild.id]["queue"].append(user)
                    if len(self.data[ctx.guild.id]["queue"]) == 10:
                        self.data[ctx.guild.id]["state"] = "pick"
                        self.data[ctx.guild.id]["blue_cap"] = random.choice(self.data[ctx.guild.id]["queue"]); self.data[ctx.guild.id]["queue"].remove(self.data[ctx.guild.id]["blue_cap"])
                        self.data[ctx.guild.id]["orange_cap"] = random.choice(self.data[ctx.guild.id]["queue"]); self.data[ctx.guild.id]["queue"].remove(self.data[ctx.guild.id]["orange_cap"])
                        self.data[ctx.guild.id]["pick_logic"] = [
                            self.data[ctx.guild.id]["blue_cap"], self.data[ctx.guild.id]["orange_cap"], self.data[ctx.guild.id]["orange_cap"], self.data[ctx.guild.id]["blue_cap"],
                            self.data[ctx.guild.id]["blue_cap"], self.data[ctx.guild.id]["orange_cap"], self.data[ctx.guild.id]["blue_cap"], self.data[ctx.guild.id]["orange_cap"]]
                        return await self.embed_gen(ctx.guild)
                    return await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id]['queue'])}/10]** {user.mention} has joined the queue", color=65535))
                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is already in the queue", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} it is not the queueing phase", color=65535))

    async def on_leave(self, ctx, user):
        if await self.check_data(ctx.guild):
            if self.data[ctx.guild.id]["state"] == "queue":
                if user in self.data[ctx.guild.id]["queue"]:
                    self.data[ctx.guild.id]["queue"].remove(user)
                    return await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id]['queue'])}/10]** {user.mention} has left the queue", color=65535))
                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not in the queue", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} it is not the queueing phase", color=65535))

    @commands.command(aliases=["p"])
    async def pick(self, ctx, user:discord.Member):
        if await self.check_data(ctx.guild):
            if self.data[ctx.guild.id]["state"] == "pick":
                if ctx.author == self.data[ctx.guild.id]["pick_logic"][0]:
                    self.data[ctx.guild.id]["pick_logic"].pop(0)
                    if self.data[ctx.guild.id]["blue_cap"] == ctx.author:
                        self.data[ctx.guild.id]["blue_team"].append(user)
                        self.data[ctx.guild.id]["queue"].remove(user)
                    else:
                        self.data[ctx.guild.id]["orange_team"].append(user)
                        self.data[ctx.guild.id]["queue"].remove(user)
                    await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has picked {user.mention}", color=65535))
                    
                    if len(self.data[ctx.guild.id]["queue"]) == 0:
                        self.data[ctx.guild.id]["state"] = "maps"
                    return await self.embed_gen(ctx.guild)
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not your turn to pick", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the picking phase", color=65535))
            
    @commands.command()
    async def map(self, ctx, map:str):
        if await self.check_data(ctx.guild):
            if ctx.author == self.data[ctx.guild.id]["blue_cap"]:
                if self.data[ctx.guild.id]["state"] == "maps":
                    for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
                        if map in str(row[1]).split(","):
                            self.data[ctx.guild.id]["map"] = map
                            self.data[ctx.guild.id]["state"] = "final"
                            return await self.embed_gen(ctx)
                        return ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} that map is not in the map pool", color=65535))
                return ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the map picking phase", color=65535))
            return ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not the blue team captain", color=65535))
        
    @commands.command(aliases=["j"])
    async def join(self, ctx):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id});").fetchall()[0] == (1,):
            return await self.on_join(ctx, ctx.author)
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is not registered"))

    @commands.command(aliases=["fj"])
    async def forcejoin(self, ctx, user:discord.Member):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
            return await self.on_join(ctx, user)

    @commands.command(aliases=["l"])
    async def leave(self, ctx):
        return await self.on_leave(ctx, ctx.author)

    @commands.command(aliases=["fl"])
    async def forceleave(self, ctx, user:discord.Member):
        return await self.on_leave(ctx, user)

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        if await self.check_data(ctx.guild):
            return await self.embed_gen(ctx)
    
    @commands.command()
    @has_permissions(manage_messages=True)
    async def clear(self, ctx):
        if await self.check_data(ctx.guild):
            await self.reset(ctx.guild)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has cleared the queue", color=65535))


def setup(client):
    client.add_cog(Queue(client))